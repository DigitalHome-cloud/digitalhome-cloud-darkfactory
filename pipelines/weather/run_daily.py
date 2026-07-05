"""Daily unattended run: trailing-window ingest → gold recompute → upload to S3.

Designed to run once and exit (container ENTRYPOINT). Idempotent: re-fetching the
trailing window overwrites those partitions (delete-then-append), so re-runs and
the ERA5 archive's ~2–5 day finalization lag are both handled.

Env:
  WEATHER_LAKE   s3://<bucket>/public/weather   (bronze read/write; used by config.py)
  GOLD_S3        s3 prefix for gold JSON        (default: $WEATHER_LAKE/gold)
  LOOKBACK_DAYS  trailing window to re-fetch    (default 10)
  AWS_*          credentials/region (mounted ~/.aws on a host, or an ECS task role)
"""
import os
import shutil
from datetime import date, timedelta

# delta-rs refuses S3 writes without a lock provider unless this is set; we are a
# single scheduled writer, so unsafe-rename is safe here.
os.environ.setdefault("AWS_S3_ALLOW_UNSAFE_RENAME", "true")

import gold_aggregate
from aq_ingest import ingest_aq_range
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
    for area in load_areas():
        try:
            print(f"  weather {area['areaId']}: {ingest_range(area, s, e)} rows", flush=True)
        except Exception as ex:
            print(f"  weather {area['areaId']} FAILED: {ex}", flush=True)
        try:
            print(f"  aq      {area['areaId']}: {ingest_aq_range(area, s, e)} rows", flush=True)
        except Exception as ex:
            print(f"  aq      {area['areaId']} skipped: {ex}", flush=True)

    print("[run_daily] recompute gold (all windows) …", flush=True)
    shutil.rmtree(gold_aggregate.GOLD_DIR, ignore_errors=True)
    gold_aggregate.main()
    upload_gold()
    print("[run_daily] done", flush=True)


if __name__ == "__main__":
    main()
