"""Gold layer — per-area renewable-siting summaries as compact JSON.

Reads the bronze Delta tables (local or WEATHER_LAKE=s3://…), computes solar/wind/
climate/rain/air-quality analytics for several averaging windows, and writes small
JSON files the Portal dashboards fetch directly. Reuses pvlib for POA transposition.

Output: {script}/gold/{areaId}/{window}/{summary,solar,wind,climate,air_quality}.json
        {script}/gold/{areaId}/water.json         (drinking water, not windowed)
        {script}/gold/index.json                  (compare view, "all" window)

Windows: all (full history) + last 10y / 5y / 3y / 1y to date.
Units: Open-Meteo wind_speed_100m is km/h → m/s; precipitation is mm.
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
PR = 0.75                        # PV performance ratio
KMH_TO_MS = 1.0 / 3.6
HOURS_PER_YEAR = 8766.0
HDD_BASE, CDD_BASE = 15.0, 22.0  # °C
WHO = {"pm2_5": 15, "pm10": 45, "nitrogen_dioxide": 25, "ozone": 100}
EAQI_PM25 = [(10, "Good"), (20, "Fair"), (25, "Moderate"),
             (50, "Poor"), (75, "Very poor"), (1e9, "Extremely poor")]
WINDOWS = [("all", None), ("10y", 10), ("5y", 5), ("3y", 3), ("1y", 1)]


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


def _nyears(df):
    """Fractional years covered — accurate annualisation for any window."""
    return max(len(df) / HOURS_PER_YEAR, 1e-9)


def load_area_weather(aid):
    df = DeltaTable(OBSERVATIONS_TABLE).to_pandas(
        columns=["time", "temperature_2m", "precipitation", "shortwave_radiation",
                 "direct_normal_irradiance", "diffuse_radiation", "solar_zenith",
                 "solar_azimuth", "wind_speed_100m", "wind_direction_100m", "date"],
        filters=[("area_id", "=", aid)],
    )
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["month"] = df["time"].dt.month
    df["hour"] = df["time"].dt.hour
    df["wind_ms"] = df["wind_speed_100m"] * KMH_TO_MS
    return df


def load_area_aq(aid):
    try:
        df = DeltaTable(AIR_QUALITY_TABLE).to_pandas(
            columns=["time", "pm2_5", "pm10", "nitrogen_dioxide", "ozone", "date"],
            filters=[("area_id", "=", aid)],
        )
    except Exception:
        return None
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df["month"] = df["time"].dt.month
    return df


def window_df(df, years, max_time):
    if years is None or df is None:
        return df
    return df[df["time"] >= (max_time - pd.DateOffset(years=years))]


# ── Solar ─────────────────────────────────────────────────────────────────────
def solar_block(df):
    ghi, dni, dhi = df["shortwave_radiation"], df["direct_normal_irradiance"], df["diffuse_radiation"]
    nyears = _nyears(df)

    daily = df.groupby([df["time"].dt.year, df["month"], df["time"].dt.day]).agg(
        ghi=("shortwave_radiation", "sum"), dni=("direct_normal_irradiance", "sum"),
        dhi=("diffuse_radiation", "sum")) / 1000.0
    daily.index.set_names(["year", "month", "day"], inplace=True)
    monthly = daily.groupby("month").mean()
    monthly_solar = {"month": list(range(1, 13)),
                     "ghi": [monthly["ghi"].get(m, np.nan) for m in range(1, 13)],
                     "dni": [monthly["dni"].get(m, np.nan) for m in range(1, 13)],
                     "dhi": [monthly["dhi"].get(m, np.nan) for m in range(1, 13)]}

    hm = df.groupby(["month", "hour"])["shortwave_radiation"].mean().unstack("hour")
    heatmap = [[float(hm.loc[m, h]) if (m in hm.index and h in hm.columns) else 0.0
                for h in range(24)] for m in range(1, 13)]

    tilts = list(range(0, 91, 5))
    poa_by_tilt = []
    for tilt in tilts:
        poa = pvlib.irradiance.get_total_irradiance(
            surface_tilt=tilt, surface_azimuth=180,
            solar_zenith=df["solar_zenith"], solar_azimuth=df["solar_azimuth"],
            dni=dni, ghi=ghi, dhi=dhi, model="isotropic")["poa_global"]
        poa_by_tilt.append(float(poa.sum()) / 1000.0 / nyears)
    opt_i = int(np.argmax(poa_by_tilt))
    optimal_tilt, annual_poa = tilts[opt_i], poa_by_tilt[opt_i]
    annual_ghi = float(ghi.sum()) / 1000.0 / nyears

    arcs = {}
    for label, mo, day in [("summer", 6, 21), ("equinox", 3, 20), ("winter", 12, 21)]:
        dd = df[(df["month"] == mo) & (df["time"].dt.day == day) & (df["solar_zenith"] < 90)]
        if len(dd):
            d = dd[dd["time"].dt.year == dd["time"].dt.year.max()].sort_values("hour")
            arcs[label] = [{"az": float(a), "el": float(90 - z), "h": int(h)}
                           for a, z, h in zip(d["solar_azimuth"], d["solar_zenith"], d["hour"])]
        else:
            arcs[label] = []

    return {"monthly": _round(monthly_solar), "heatmap": _round(heatmap, 0),
            "tilt_curve": {"tilt": tilts, "poa": _round(poa_by_tilt)},
            "sun_path": _round(arcs), "optimal_tilt": optimal_tilt,
            "annual_poa_kwh_m2": round(annual_poa, 1),
            "annual_ghi_kwh_m2": round(annual_ghi, 1),
            "pv_yield_kwh_kwp": round(annual_poa * PR, 1)}


# ── Wind (100 m, m/s) ─────────────────────────────────────────────────────────
def turbine_cf(v):
    ci, rated, co = 3.0, 12.0, 25.0
    p = np.where(v < ci, 0.0, np.where(v < rated, (v ** 3 - ci ** 3) / (rated ** 3 - ci ** 3),
                                       np.where(v < co, 1.0, 0.0)))
    return float(np.nanmean(p))


def wind_block(df):
    vw, dw = df["wind_ms"].to_numpy(), df["wind_direction_100m"].to_numpy()
    mask = ~np.isnan(vw) & ~np.isnan(dw)
    v, d = vw[mask], dw[mask]
    sectors = (((d + 22.5) // 45) % 8).astype(int)
    speed_bins = [0, 3, 6, 9, 12, 100]
    sb = np.clip(np.digitize(v, speed_bins) - 1, 0, len(speed_bins) - 2)
    rose = np.zeros((8, len(speed_bins) - 1))
    for s, b in zip(sectors, sb):
        rose[s, b] += 1
    rose = rose / max(rose.sum(), 1) * 100.0
    hist, edges = np.histogram(v, bins=np.arange(0, 26, 1), density=True)
    k, _, c = stats.weibull_min.fit(v[v > 0], floc=0)
    monthly = df.groupby("month")["wind_ms"].mean()
    return {"rose": {"dirs": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                     "speed_bins": ["0–3", "3–6", "6–9", "9–12", "12+"],
                     "matrix": _round(rose.tolist())},
            "hist": {"edges": edges[:-1].tolist(), "density": _round(hist.tolist(), 4)},
            "weibull": {"k": round(float(k), 2), "c": round(float(c), 2)},
            "monthly_mean_ms": _round([float(monthly.get(m, np.nan)) for m in range(1, 13)]),
            "mean_ms": round(float(np.mean(v)), 2),
            "capacity_factor_pct": round(turbine_cf(v) * 100, 1)}


# ── Climate + rain ────────────────────────────────────────────────────────────
def climate_block(df):
    t = df["temperature_2m"]
    nyears = _nyears(df)
    daily = df.groupby("date").agg(tmin=("temperature_2m", "min"),
                                   tmean=("temperature_2m", "mean"),
                                   tmax=("temperature_2m", "max"),
                                   month=("month", "first"))
    mtemp = daily.groupby("month")[["tmin", "tmean", "tmax"]].mean()  # typical (normals)
    daily["hdd"] = np.maximum(0, HDD_BASE - daily["tmean"])
    daily["cdd"] = np.maximum(0, daily["tmean"] - CDD_BASE)
    mdd = daily.groupby("month")[["hdd", "cdd"]].sum() / nyears
    sorted_t = np.sort(t.to_numpy())[::-1]
    idx = np.linspace(0, len(sorted_t) - 1, 200).astype(int)
    return {"monthly": {"month": list(range(1, 13)),
                        "min": _round([mtemp["tmin"].get(m, np.nan) for m in range(1, 13)]),
                        "mean": _round([mtemp["tmean"].get(m, np.nan) for m in range(1, 13)]),
                        "max": _round([mtemp["tmax"].get(m, np.nan) for m in range(1, 13)]),
                        "hdd": _round([float(mdd["hdd"].get(m, 0)) for m in range(1, 13)], 0),
                        "cdd": _round([float(mdd["cdd"].get(m, 0)) for m in range(1, 13)], 0)},
            "hdd": round(float(daily["hdd"].sum()) / nyears, 0),
            "cdd": round(float(daily["cdd"].sum()) / nyears, 0),
            "duration_curve": _round(sorted_t[idx].tolist(), 1),
            "mean_temp_c": round(float(t.mean()), 1)}


def rain_block(df):
    nyears = _nyears(df)
    daily = df.groupby("date").agg(p=("precipitation", "sum"), month=("month", "first"))
    mtot = daily.groupby("month")["p"].sum() / nyears
    return {"monthly_mm": _round([float(mtot.get(m, 0)) for m in range(1, 13)], 1),
            "annual_mm": round(float(daily["p"].sum()) / nyears, 0),
            "wet_days": int(round((daily["p"] > 1.0).sum() / nyears)),
            "dry_days": int(round((daily["p"] <= 1.0).sum() / nyears)),
            "max_daily_mm": round(float(daily["p"].max()), 1)}


# ── Air quality ───────────────────────────────────────────────────────────────
def air_quality_block(df):
    if df is None or len(df) == 0:
        return None, {"mean_pm25": None, "aqi_band": "n/a"}
    pollutants = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone"]
    monthly = {p: _round([df[df["month"] == m][p].mean() for m in range(1, 13)]) for p in pollutants}
    daily = df.groupby("date")[pollutants].mean()
    nyears = max(len(df) / HOURS_PER_YEAR, 1e-9)
    days_over = {p: int(round((daily[p] > WHO[p]).sum() / nyears)) for p in pollutants}
    mean_pm25 = float(df["pm2_5"].mean())
    band = next(lbl for thr, lbl in EAQI_PM25 if mean_pm25 <= thr)
    return ({"monthly": {"month": list(range(1, 13)), **monthly}, "days_over_who": days_over,
             "span": [str(df["date"].min()), str(df["date"].max())]},
            {"mean_pm25": round(mean_pm25, 1), "aqi_band": band})


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
        wdf = load_area_weather(aid)
        aqdf = load_area_aq(aid)
        wmax = wdf["time"].max()
        aqmax = aqdf["time"].max() if aqdf is not None else None

        for wname, years in WINDOWS:
            df = window_df(wdf, years, wmax)
            if len(df) < 24:
                continue
            solar, wind = solar_block(df), wind_block(df)
            climate = climate_block(df)
            climate["rain"] = rain_block(df)
            aq, aq_summary = air_quality_block(window_df(aqdf, years, aqmax))

            gdir = os.path.join(GOLD_DIR, aid, wname)
            write_json(os.path.join(gdir, "solar.json"), solar)
            write_json(os.path.join(gdir, "wind.json"), wind)
            write_json(os.path.join(gdir, "climate.json"), climate)
            if aq:
                write_json(os.path.join(gdir, "air_quality.json"), aq)
            summary = {"areaId": aid, "name": area["name"], "window": wname,
                       "latitude": area["latitude"], "longitude": area["longitude"],
                       "span_weather": [str(df["date"].min()), str(df["date"].max())],
                       "pv_yield_kwh_kwp": solar["pv_yield_kwh_kwp"],
                       "optimal_tilt_deg": solar["optimal_tilt"],
                       "annual_ghi_kwh_m2": solar["annual_ghi_kwh_m2"],
                       "wind_cf_pct": wind["capacity_factor_pct"],
                       "mean_wind_100m_ms": wind["mean_ms"],
                       "mean_temp_c": climate["mean_temp_c"],
                       "annual_rain_mm": climate["rain"]["annual_mm"],
                       "hdd": climate["hdd"], "cdd": climate["cdd"], **aq_summary}
            write_json(os.path.join(gdir, "summary.json"), summary)
            if wname == "all":
                index.append(summary)

        # Drinking water — best-effort, not windowed (periodic samples).
        try:
            from drinking_water import fetch_water
            water = fetch_water(area)
        except Exception as e:
            print(f"    water skipped: {e}", flush=True)
            water = None
        if water:
            write_json(os.path.join(GOLD_DIR, aid, "water.json"), water)

    write_json(os.path.join(GOLD_DIR, "index.json"), index)
    print(f"gold written -> {GOLD_DIR}  ({len(index)} areas × {len(WINDOWS)} windows)")


if __name__ == "__main__":
    main()
