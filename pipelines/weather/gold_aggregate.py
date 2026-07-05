"""Gold layer — per-area renewable-siting summaries as compact JSON.

Reads the bronze Delta tables (local or WEATHER_LAKE=s3://…), computes solar/wind/
climate/air-quality analytics, and writes small JSON files the Portal dashboards
fetch directly. Reuses pvlib for plane-of-array (tilt) transposition.

Output: {script}/gold/{areaId}/{summary,solar,wind,climate,air_quality}.json
        {script}/gold/index.json   (compare view)

Units note: Open-Meteo wind_speed_100m is km/h → converted to m/s here.
"""
import json
import os

import numpy as np
import pandas as pd
import pvlib
from deltalake import DeltaTable
from scipy import stats

from config import AIR_QUALITY_TABLE, AREAS_FILE, OBSERVATIONS_TABLE

GOLD_DIR = os.path.join(os.path.dirname(__file__), "gold")
PR = 0.75                       # PV performance ratio
KMH_TO_MS = 1.0 / 3.6
HOURS_PER_YEAR = 8766.0
HDD_BASE, CDD_BASE = 15.0, 22.0  # °C
# WHO 2021 24-h guideline values (µg/m³); O3 is 8-h but we approximate on daily mean
WHO = {"pm2_5": 15, "pm10": 45, "nitrogen_dioxide": 25, "ozone": 100}
EAQI_PM25 = [(10, "Good"), (20, "Fair"), (25, "Moderate"),
             (50, "Poor"), (75, "Very poor"), (1e9, "Extremely poor")]


def _round(o, n=2):
    if isinstance(o, dict):
        return {k: _round(v, n) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_round(v, n) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else round(float(o), n)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


def load_area_weather(aid):
    df = DeltaTable(OBSERVATIONS_TABLE).to_pandas(
        columns=["time", "temperature_2m", "shortwave_radiation",
                 "direct_normal_irradiance", "diffuse_radiation",
                 "solar_zenith", "solar_azimuth", "wind_speed_100m",
                 "wind_direction_100m", "date"],
        filters=[("area_id", "=", aid)],
    )
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["month"] = df["time"].dt.month
    df["hour"] = df["time"].dt.hour
    df["wind_ms"] = df["wind_speed_100m"] * KMH_TO_MS
    df["n_years"] = df["time"].dt.year.nunique()
    return df


# ── Solar ─────────────────────────────────────────────────────────────────────
def solar_block(df):
    ghi, dni, dhi = df["shortwave_radiation"], df["direct_normal_irradiance"], df["diffuse_radiation"]
    nyears = df["n_years"].iloc[0]

    # monthly mean daily kWh/m² for GHI/DNI/DHI
    daily = df.groupby([df["time"].dt.year, df["month"], df["time"].dt.day]).agg(
        ghi=("shortwave_radiation", "sum"),
        dni=("direct_normal_irradiance", "sum"),
        dhi=("diffuse_radiation", "sum"),
    ) / 1000.0
    daily.index.set_names(["year", "month", "day"], inplace=True)
    monthly = daily.groupby("month").mean()
    monthly_solar = {
        "month": list(range(1, 13)),
        "ghi": [monthly["ghi"].get(m, np.nan) for m in range(1, 13)],
        "dni": [monthly["dni"].get(m, np.nan) for m in range(1, 13)],
        "dhi": [monthly["dhi"].get(m, np.nan) for m in range(1, 13)],
    }

    # hour × month mean GHI (W/m²) heatmap
    hm = df.groupby(["month", "hour"])["shortwave_radiation"].mean().unstack("hour")
    heatmap = [[float(hm.loc[m, h]) if (m in hm.index and h in hm.columns) else 0.0
                for h in range(24)] for m in range(1, 13)]

    # tilt → annual POA (kWh/m²) sweep, south-facing (azimuth 180)
    tilts = list(range(0, 91, 5))
    poa_by_tilt = []
    for tilt in tilts:
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt, surface_azimuth=180,
            solar_zenith=df["solar_zenith"], solar_azimuth=df["solar_azimuth"],
            dni=dni, ghi=ghi, dhi=dhi, model="isotropic",
        )["poa_global"]
        poa_by_tilt.append(float(poa.sum()) / 1000.0 / nyears)
    opt_i = int(np.argmax(poa_by_tilt))
    optimal_tilt = tilts[opt_i]
    annual_poa = poa_by_tilt[opt_i]
    annual_ghi = float(ghi.sum()) / 1000.0 / nyears
    pv_yield = annual_poa * PR

    # sun-path arcs for representative days (use latest full year available)
    yr = int(df["time"].dt.year.max()) - 1
    arcs = {}
    for label, mo, day in [("summer", 6, 21), ("equinox", 3, 20), ("winter", 12, 21)]:
        d = df[(df["time"].dt.year == yr) & (df["month"] == mo) & (df["time"].dt.day == day)]
        d = d[d["solar_zenith"] < 90].sort_values("hour")
        arcs[label] = [{"az": float(a), "el": float(90 - z), "h": int(h)}
                       for a, z, h in zip(d["solar_azimuth"], d["solar_zenith"], d["hour"])]

    return {
        "monthly": _round(monthly_solar),
        "heatmap": _round(heatmap, 0),
        "tilt_curve": {"tilt": tilts, "poa": _round(poa_by_tilt)},
        "sun_path": _round(arcs),
        "optimal_tilt": optimal_tilt,
        "annual_poa_kwh_m2": round(annual_poa, 1),
        "annual_ghi_kwh_m2": round(annual_ghi, 1),
        "pv_yield_kwh_kwp": round(pv_yield, 1),
    }


# ── Wind (100 m, m/s) ─────────────────────────────────────────────────────────
def turbine_cf(v):
    ci, rated, co = 3.0, 12.0, 25.0
    p = np.where(v < ci, 0.0,
        np.where(v < rated, (v ** 3 - ci ** 3) / (rated ** 3 - ci ** 3),
        np.where(v < co, 1.0, 0.0)))
    return float(np.nanmean(p))


def wind_block(df):
    vw = df["wind_ms"].to_numpy()
    dw = df["wind_direction_100m"].to_numpy()
    mask = ~np.isnan(vw) & ~np.isnan(dw)
    v, d = vw[mask], dw[mask]

    # wind rose: 8 dir sectors (45°) × 5 speed bins, % of time
    sectors = (((d + 22.5) // 45) % 8).astype(int)
    speed_bins = [0, 3, 6, 9, 12, 100]
    sb = np.clip(np.digitize(v, speed_bins) - 1, 0, len(speed_bins) - 2)
    rose = np.zeros((8, len(speed_bins) - 1))
    for s, b in zip(sectors, sb):
        rose[s, b] += 1
    rose = rose / max(rose.sum(), 1) * 100.0   # percent of time

    hist, edges = np.histogram(v, bins=np.arange(0, 26, 1), density=True)
    k, _, c = stats.weibull_min.fit(v[v > 0], floc=0)
    monthly = df.groupby("month")["wind_ms"].mean()
    return {
        "rose": {
            "dirs": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
            "speed_bins": ["0–3", "3–6", "6–9", "9–12", "12+"],
            "matrix": _round(rose.tolist()),
        },
        "hist": {"edges": edges[:-1].tolist(), "density": _round(hist.tolist(), 4)},
        "weibull": {"k": round(float(k), 2), "c": round(float(c), 2)},
        "monthly_mean_ms": _round([float(monthly.get(m, np.nan)) for m in range(1, 13)]),
        "mean_ms": round(float(np.mean(v)), 2),
        "capacity_factor_pct": round(turbine_cf(v) * 100, 1),
    }


# ── Climate ───────────────────────────────────────────────────────────────────
def climate_block(df):
    t = df["temperature_2m"]
    nyears = df["n_years"].iloc[0]
    monthly = df.groupby("month")["temperature_2m"].agg(["min", "mean", "max"])
    daily = df.groupby("date").agg(tmean=("temperature_2m", "mean"),
                                   month=("month", "first"))
    daily["hdd"] = np.maximum(0, HDD_BASE - daily["tmean"])
    daily["cdd"] = np.maximum(0, daily["tmean"] - CDD_BASE)
    mdd = daily.groupby("month")[["hdd", "cdd"]].sum() / nyears
    hdd = float(daily["hdd"].sum()) / nyears
    cdd = float(daily["cdd"].sum()) / nyears
    # duration curve subsampled to ~180 points
    sorted_t = np.sort(t.to_numpy())[::-1]
    idx = np.linspace(0, len(sorted_t) - 1, 180).astype(int)
    return {
        "monthly": {
            "month": list(range(1, 13)),
            "min": _round([monthly["min"].get(m, np.nan) for m in range(1, 13)]),
            "mean": _round([monthly["mean"].get(m, np.nan) for m in range(1, 13)]),
            "max": _round([monthly["max"].get(m, np.nan) for m in range(1, 13)]),
            "hdd": _round([float(mdd["hdd"].get(m, 0)) for m in range(1, 13)], 0),
            "cdd": _round([float(mdd["cdd"].get(m, 0)) for m in range(1, 13)], 0),
        },
        "hdd": round(hdd, 0), "cdd": round(cdd, 0),
        "duration_curve": _round(sorted_t[idx].tolist(), 1),
        "mean_temp_c": round(float(t.mean()), 1),
    }


# ── Air quality ───────────────────────────────────────────────────────────────
def air_quality_block(aid):
    try:
        df = DeltaTable(AIR_QUALITY_TABLE).to_pandas(
            columns=["time", "pm2_5", "pm10", "nitrogen_dioxide", "ozone", "date"],
            filters=[("area_id", "=", aid)],
        )
    except Exception:
        return None, {"mean_pm25": None, "aqi_band": "n/a"}
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["month"] = df["time"].dt.month
    pollutants = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone"]
    monthly = {p: _round([df[df["month"] == m][p].mean() for m in range(1, 13)]) for p in pollutants}
    daily = df.groupby("date")[pollutants].mean()
    nyears = df["time"].dt.year.nunique()
    days_over = {p: int((daily[p] > WHO[p]).sum() / nyears) for p in pollutants}
    mean_pm25 = float(df["pm2_5"].mean())
    band = next(lbl for thr, lbl in EAQI_PM25 if mean_pm25 <= thr)
    block = {
        "monthly": {"month": list(range(1, 13)), **monthly},
        "days_over_who": days_over,
        "span": [str(df["date"].min()), str(df["date"].max())],
    }
    return block, {"mean_pm25": round(mean_pm25, 1), "aqi_band": band}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, separators=(",", ":"))


def main():
    areas = json.load(open(AREAS_FILE))
    index = []
    for area in areas:
        aid = area["areaId"]
        print(f"  {aid} …", flush=True)
        df = load_area_weather(aid)
        solar = solar_block(df)
        wind = wind_block(df)
        climate = climate_block(df)
        aq, aq_summary = air_quality_block(aid)

        gdir = os.path.join(GOLD_DIR, aid)
        write_json(os.path.join(gdir, "solar.json"), solar)
        write_json(os.path.join(gdir, "wind.json"), wind)
        write_json(os.path.join(gdir, "climate.json"), climate)
        if aq:
            write_json(os.path.join(gdir, "air_quality.json"), aq)

        summary = {
            "areaId": aid, "name": area["name"],
            "latitude": area["latitude"], "longitude": area["longitude"],
            "span_weather": [str(df["date"].min()), str(df["date"].max())],
            "pv_yield_kwh_kwp": solar["pv_yield_kwh_kwp"],
            "optimal_tilt_deg": solar["optimal_tilt"],
            "annual_ghi_kwh_m2": solar["annual_ghi_kwh_m2"],
            "wind_cf_pct": wind["capacity_factor_pct"],
            "mean_wind_100m_ms": wind["mean_ms"],
            "mean_temp_c": climate["mean_temp_c"],
            "hdd": climate["hdd"], "cdd": climate["cdd"],
            **aq_summary,
        }
        write_json(os.path.join(gdir, "summary.json"), summary)
        index.append(summary)

    write_json(os.path.join(GOLD_DIR, "index.json"), index)
    print(f"gold written -> {GOLD_DIR}  ({len(index)} areas)")


if __name__ == "__main__":
    main()
