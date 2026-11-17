"""Daily unattended run: trailing-window ingest → gold recompute → upload to S3.

Designed to run once and exit (container ENTRYPOINT). Idempotent: re-fetching the
trailing window overwrites those partitions (delete-then-append), so re-runs and
the ERA5 archive's ~2–5 day finalization lag are both handled.

Env:
  WEATHER_LAKE   s3://<bucket>/public/weather   (bronze read/write; used by config.py)
  GOLD_S3        s3 prefix for gold JSON        (default: $WEATHER_LAKE/gold)
  LOOKBACK_DAYS  trailing window to re-fetch    (default 10)
  AREA_TABLE     the backend's DynamoDB Area table; its areas are the ones
                 ingested, and each area's lastIngestedAt is set when it is
                 complete (unset: areas.json)

Every run first fills each area's missing past years (a new area's whole
history, or one a rate limit cut short; complete years cost nothing), then
re-fetches the trailing window.
  AWS_*          credentials/region (mounted ~/.aws on a host, or an ECS task role)
"""
import os
import shutil
from datetime import date, datetime, timedelta, timezone

# delta-rs refuses S3 writes without a lock provider unless this is set; we are a
# single scheduled writer, so unsafe-rename is safe here.
os.environ.setdefault("AWS_S3_ALLOW_UNSAFE_RENAME", "true")

import gold_aggregate
from aq_ingest import ingest_aq_range
from backfill import backfill_area, existing_counts
from config import AIR_QUALITY_TABLE, OBSERVATIONS_TABLE, mark_ingested
from weather_ingest import ingest_range, load_areas

LOOKBACK = int(os.environ.get("LOOKBACK_DAYS", "10"))


def upload_gold():
    import boto3

    gold_s3 = os.environ.get("GOLD_S3") or (os.environ["WEATHER_LAKE"].rstrip("/") + "/gold")
    assert gold_s3.startswith("s3://"), "GOLD_S3 / WEATHER_LAKE must be an s3:// URI"
    bucket, prefix = gold_s3[5:].split("/", 1)
    s3 = boto3.client("s3")
    root = gold_aggregate.GOLD_DIR
    n = 0
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".json"):
                continue
            local = os.path.join(dirpath, f)
            key = f"{prefix.rstrip('/')}/{os.path.relpath(local, root)}"
            s3.upload_file(local, bucket, key, ExtraArgs={"ContentType": "application/json"})
            n += 1
    print(f"[run_daily] uploaded {n} gold files → {gold_s3}", flush=True)


def main():
    end = date.today()
    start = end - timedelta(days=LOOKBACK)
    s, e = start.isoformat(), end.isoformat()
    print(f"[run_daily] ingest window {s}..{e} (lookback {LOOKBACK}d)", flush=True)
    areas = load_areas()
    print(f"[run_daily] {len(areas)} areas: {', '.join(a['areaId'] for a in areas)}", flush=True)
    counts = {"weather": existing_counts(OBSERVATIONS_TABLE), "aq": existing_counts(AIR_QUALITY_TABLE)}
    fresh = []
    for area in areas:
        aid = area["areaId"]
        try:
            n = backfill_area("weather", area, counts=counts["weather"], past_only=True)
            if n:
                print(f"  weather {aid}: {n} rows of missing history", flush=True)
            print(f"  weather {aid}: {ingest_range(area, s, e)} rows", flush=True)
            fresh.append(aid)
        except Exception as ex:
            print(f"  weather {aid} FAILED (the next run goes on from here): {ex}", flush=True)
        try:
            n = backfill_area("aq", area, counts=counts["aq"], past_only=True)
            if n:
                print(f"  aq      {aid}: {n} rows of missing history", flush=True)
            print(f"  aq      {aid}: {ingest_aq_range(area, s, e)} rows", flush=True)
        except Exception as ex:
            print(f"  aq      {aid} skipped: {ex}", flush=True)

    print("[run_daily] recompute gold (all windows) …", flush=True)
    shutil.rmtree(gold_aggregate.GOLD_DIR, ignore_errors=True)
    gold_aggregate.main()
    upload_gold()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    for aid in fresh:
        try:
            mark_ingested(aid, now)
        except Exception as ex:
            print(f"  {aid}: lastIngestedAt not set: {ex}", flush=True)
    print("[run_daily] done", flush=True)


if __name__ == "__main__":
    main()
