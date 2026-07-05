"""Fetch + write hourly air-quality (pollution) observations per area.

Separate table from weather: the CAMS reanalysis only reaches back to 2013
(vs ERA5 weather to 2000), so it has its own history and its own table.
"""
import json
import sys

import pandas as pd

from config import (AIR_QUALITY_TABLE, AIR_QUALITY_URL, AIR_QUALITY_VARS,
                    AREAS_FILE)
from fetch_openmeteo import request_json  # shared GET-json + 429 backoff
from lake_io import write_partitioned


def load_areas():
    with open(AREAS_FILE) as f:
        return json.load(f)


def fetch_aq(area, start_date, end_date):
    params = {
        "latitude": area["latitude"],
        "longitude": area["longitude"],
        "start_date": start_date,
        "end_date": end_date,
        "hourly": AIR_QUALITY_VARS,
        "timezone": "UTC",
    }
    data = request_json(AIR_QUALITY_URL, params)
    hourly = data.get("hourly") or {}
    if not hourly.get("time"):
        return pd.DataFrame()
    df = pd.DataFrame(hourly)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    for var in AIR_QUALITY_VARS:
        if var not in df.columns:
            df[var] = pd.NA
    df["area_id"] = area["areaId"]
    df["year"] = df["time"].dt.year.astype("int32")
    df["date"] = df["time"].dt.strftime("%Y-%m-%d")
    return df[["time"] + AIR_QUALITY_VARS + ["area_id", "year", "date"]]


def ingest_aq_range(area, start_date, end_date):
    return write_partitioned(fetch_aq(area, start_date, end_date), AIR_QUALITY_TABLE, AIR_QUALITY_VARS)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: aq_ingest.py START_DATE END_DATE   (YYYY-MM-DD, inclusive, UTC)")
        raise SystemExit(1)
    start, end = sys.argv[1], sys.argv[2]
    total = 0
    for area in load_areas():
        n = ingest_aq_range(area, start, end)
        total += n
        print(f"  {area['areaId']:<10} {start}..{end}  {n:>6} rows")
    print(f"total {total} rows -> {AIR_QUALITY_TABLE}")
