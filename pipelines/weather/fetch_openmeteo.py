"""Fetch hourly weather for one area from the Open-Meteo historical archive.

Returns a tidy pandas DataFrame: UTC time, the HOURLY_VARS, the COMPUTED sun
position (elevation/azimuth/zenith), plus area_id, year, date partition columns.
"""
import time as _time

import pandas as pd

try:
    import requests

    def _get_json(url, params):
        r = requests.get(url, params=params, timeout=60)
        r.raise_for_status()
        return r.json()
except ImportError:  # stdlib fallback
    import json
    import urllib.parse
    import urllib.request

    def _get_json(url, params):
        flat = [(k, ",".join(v) if isinstance(v, list) else v) for k, v in params.items()]
        with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(flat), timeout=60) as resp:
            return json.loads(resp.read().decode())

from config import ARCHIVE_URL, HOURLY_VARS
from solar import sun_position


def request_json(url, params, retries=8):
    """GET with rate-limit-aware backoff. Open-Meteo's free tier weights requests
    by variables×span; on 429 we wait a full minute for the window to reset."""
    last_err = None
    for attempt in range(retries):
        try:
            return _get_json(url, params)
        except Exception as e:
            last_err = e
            wait = 60 if "429" in str(e) else 3 * (attempt + 1)
            _time.sleep(wait)
    raise RuntimeError(f"fetch failed after {retries} tries: {last_err}")


def fetch_area(area, start_date, end_date):
    """area: dict with areaId, latitude, longitude. Times returned in UTC."""
    params = {
        "latitude": area["latitude"],
        "longitude": area["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": HOURLY_VARS,
        "timezone": "UTC",
    }
    data = request_json(ARCHIVE_URL, params)
    hourly = data.get("hourly") or {}
    if not hourly.get("time"):
        return pd.DataFrame()

    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    for var in HOURLY_VARS:
        if var not in df.columns:
            df[var] = pd.NA

    # Sun angle in the sky — computed, not fetched (for panel tilt/orientation).
    sp = sun_position(df["time"], area["latitude"], area["longitude"])
    df = pd.concat([df.reset_index(drop=True), sp.reset_index(drop=True)], axis=1)

    df["area_id"] = area["areaId"]
    df["year"] = df["time"].dt.year.astype("int32")
    df["date"] = df["time"].dt.strftime("%Y-%m-%d")  # UTC date
    ordered = ["time"] + HOURLY_VARS + list(sp.columns) + ["area_id", "year", "date"]
    return df[ordered]


if __name__ == "__main__":
    import json

    with open("areas.json") as f:
        a = json.load(f)[0]
    d = fetch_area(a, "2024-06-21", "2024-06-21")
    print(d.shape)
    print(d[["time", "temperature_2m", "direct_normal_irradiance",
             "wind_speed_100m", "solar_elevation", "solar_azimuth"]].iloc[9:14].to_string())
