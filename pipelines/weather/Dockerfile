# Weather/renewables pipeline — daily ingest + gold recompute + S3 upload.
# Runs once and exits (spare PC via cron/systemd, or AWS ECS Fargate scheduled task).
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py areas.json manifest.json ./

# Config via env: WEATHER_LAKE (s3://…/public/weather), GOLD_S3, LOOKBACK_DAYS, AWS_*.
ENTRYPOINT ["python", "run_daily.py"]
