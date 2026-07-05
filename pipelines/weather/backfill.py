"""One-time historical backfill, chunked by calendar year. Idempotent.

Usage:
    python backfill.py                 # both products, default starts
    python backfill.py weather         # weather only (ERA5, from 2000)
    python backfill.py aq              # air quality only (CAMS, from 2013)
    python backfill.py weather 2010-01-01   # custom start

Open-Meteo's archives take year-sized requests fine; we sleep briefly between
calls to stay under the free rate limit.
"""
import sys
import time
from datetime import date

from deltalake import DeltaTable

from config import (AIR_QUALITY_START, AIR_QUALITY_TABLE, OBSERVATIONS_TABLE,
                    WEATHER_START)
from aq_ingest import ingest_aq_range
from weather_ingest import ingest_range as ingest_weather_range, load_areas

PRODUCTS = {
    "weather": (ingest_weather_range, WEATHER_START, OBSERVATIONS_TABLE),
    "aq": (ingest_aq_range, AIR_QUALITY_START, AIR_QUALITY_TABLE),
}
FULL_YEAR_ROWS = 8000  # a complete hourly year is ~8760; treat >= this as "done"


def year_chunks(start_iso, end_date):
    start = date.fromisoformat(start_iso)
    y = start.year
    while y <= end_date.year:
        yield (max(date(y, 1, 1), start).isoformat(),
               min(date(y, 12, 31), end_date).isoformat())
        y += 1


def existing_counts(table):
    """{(area_id, year): rows} already stored — lets a re-run resume, skipping
    complete past years without re-hitting the API."""
    try:
        df = DeltaTable(table).to_pandas(columns=["area_id", "year"])
    except Exception:
        return {}
    return {(a, int(y)): c for (a, y), c in df.value_counts(["area_id", "year"]).items()}


def run(product, start_iso):
    ingest, default_start, table = PRODUCTS[product]
    start_iso = start_iso or default_start
    today = date.today()
    counts = existing_counts(table)
    grand = 0
    for area in load_areas():
        aid = area["areaId"]
        area_total = 0
        for c_start, c_end in year_chunks(start_iso, today):
            yr = int(c_start[:4])
            # Skip complete past years; always refresh the current (growing) year.
            if yr < today.year and counts.get((aid, yr), 0) >= FULL_YEAR_ROWS:
                print(f"  [{product}] {aid:<10} {yr}  skip (present)")
                continue
            n = ingest(area, c_start, c_end)
            area_total += n
            print(f"  [{product}] {aid:<10} {yr}  {n:>5} rows")
            time.sleep(2)
        print(f"= [{product}] {aid} added {area_total} rows")
        grand += area_total
    print(f"[{product}] complete: added {grand} rows -> {table}\n")


if __name__ == "__main__":
    product = sys.argv[1] if len(sys.argv) > 1 else "all"
    start = sys.argv[2] if len(sys.argv) > 2 else None
    for p in (["weather", "aq"] if product == "all" else [product]):
        run(p, start)
