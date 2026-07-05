"""Summary + sample reads for the weather and air-quality lakes."""
import os

from deltalake import DeltaTable

from config import AIR_QUALITY_TABLE, OBSERVATIONS_TABLE


def _dir_size(path):
    if not os.path.isdir(path):
        return 0
    return sum(os.path.getsize(os.path.join(r, f))
               for r, _, fs in os.walk(path) for f in fs)


def summarize(table, cols, label):
    try:
        dt = DeltaTable(table)
    except Exception:
        print(f"{label}: (not built)\n")
        return
    df = dt.to_pandas(columns=cols)
    print(f"{label}  ({table})")
    print(f"  rows {len(df):,} | span {df['date'].min()}..{df['date'].max()} "
          f"| size {_dir_size(table)/1e6:.2f} MB")
    for aid, g in df.groupby("area_id"):
        extra = " | ".join(f"{c}~{g[c].mean():.1f}" for c in cols
                           if c not in ("area_id", "date", "time"))
        print(f"    {aid:<10} {len(g):>7,} rows  {g['date'].min()[:4]}..{g['date'].max()[:4]}  {extra}")
    print()


if __name__ == "__main__":
    summarize(OBSERVATIONS_TABLE,
              ["area_id", "date", "temperature_2m", "shortwave_radiation",
               "wind_speed_100m", "solar_elevation"],
              "WEATHER")
    summarize(AIR_QUALITY_TABLE,
              ["area_id", "date", "pm2_5", "nitrogen_dioxide", "ozone"],
              "AIR QUALITY")

    # Example: solar-siting slice for one area (sun up only)
    try:
        dt = DeltaTable(OBSERVATIONS_TABLE)
        s = dt.to_pandas(
            columns=["area_id", "date", "solar_elevation", "direct_normal_irradiance"],
            filters=[("area_id", "=", "DE-39576"), ("year", ">=", 2024)],
        )
        s = s[s["solar_elevation"] > 0]
        print(f"DE-39576 daylight hours 2024+: {len(s):,} | "
              f"mean DNI {s['direct_normal_irradiance'].mean():.0f} W/m² | "
              f"mean sun elevation {s['solar_elevation'].mean():.1f}°")
    except Exception as e:
        print("sample read skipped:", e)
