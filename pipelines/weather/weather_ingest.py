"""Write hourly weather observations (incl. solar position) to the bronze table."""
import json
import sys

from config import (AREAS_FILE, HOURLY_VARS, OBSERVATIONS_TABLE, SOLAR_POSITION_COLS)
from fetch_openmeteo import fetch_area
from lake_io import write_partitioned

NUMERIC_COLS = HOURLY_VARS + SOLAR_POSITION_COLS


def load_areas():
    with open(AREAS_FILE) as f:
        return json.load(f)


def ingest_range(area, start_date, end_date):
    df = fetch_area(area, start_date, end_date)
    return write_partitioned(df, OBSERVATIONS_TABLE, NUMERIC_COLS)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: weather_ingest.py START_DATE END_DATE   (YYYY-MM-DD, inclusive, UTC)")
        raise SystemExit(1)
    start, end = sys.argv[1], sys.argv[2]
    total = 0
    for area in load_areas():
        n = ingest_range(area, start, end)
        total += n
        print(f"  {area['areaId']:<10} {start}..{end}  {n:>6} rows")
    print(f"total {total} rows -> {OBSERVATIONS_TABLE}")
