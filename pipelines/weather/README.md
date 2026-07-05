# Area weather data lake

Hourly weather per **Area** (`{country}-{postalCode}`, e.g. `DE-39576`), stored
as a Delta Lake table. Weather is keyed by area, never by SmartHome — many homes
share one area, and a `DigitalHome` already carries `country`+`postalCode`.

Reference stack (matches `../../experimental/data`): delta-rs (`deltalake==1.5.1`) + pandas +
pyarrow. Provider: **Open-Meteo** historical archive (ERA5) — free, no API key.

## Layout
- `config.py` — variables, table path (`WEATHER_LAKE` env, local by default)
- `areas.json` — the 3 seed areas + centroid lat/lon + timezone
- `fetch_openmeteo.py` / `weather_ingest.py` — fetch + write bronze weather (idempotent)
- `aq_ingest.py` — air-quality (CAMS, from 2013)
- `backfill.py` — one-time historical load, chunked by year
- `gold_aggregate.py` — per-area solar/wind/climate/rain/AQ **gold JSON**, per window
  (`all / 10y / 5y / 3y / 1y`) → `gold/{areaId}/{window}/*.json` (+ `index.json`)
- `drinking_water.py` — FR tap-water quality via Hub'Eau (best-effort) → `gold/{areaId}/water.json`
- `run_daily.py` — **daily orchestrator**: trailing-window ingest → gold → upload to S3
- `read_weather.py` — summary + sample filtered read
- `manifest.json` — column → Brick class + QUDT unit

## Daily run (Docker — spare PC now, ECS Fargate later)
```bash
docker build -t dhc-weather-pipeline pipelines/weather
docker run --rm \
  -e WEATHER_LAKE=s3://<bucket>/public/weather \
  -e GOLD_S3=s3://<bucket>/public/weather/gold \
  -e LOOKBACK_DAYS=10 \
  -v ~/.aws:/root/.aws:ro \
  dhc-weather-pipeline
```
Schedule with a systemd `.timer` (PC) or **EventBridge Scheduler → ECS RunTask** on
Fargate (task role scoped to `public/weather/*`; default-VPC public subnet + public IP
for API egress). `LOOKBACK_DAYS=10` re-fetches a trailing window each run because the
ERA5 archive finalizes ~2–5 days late (idempotent overwrite).

## Run
```bash
# from repo root, using the shared venv
.venv/bin/pip install -r pipelines/weather/requirements.txt
cd pipelines/weather
../../.venv/bin/python backfill.py 2020-01-01     # historical backfill
../../.venv/bin/python read_weather.py            # verify: rows, span, size
# daily append (cron): python weather_ingest.py <YESTERDAY> <TODAY>
```

## Target S3 (later)
```bash
export WEATHER_LAKE=s3://<dhcStorage-bucket>/public/weather   # + AWS_* creds
```
The table is written under `public/weather/observations/` (area weather is shared
/ world-readable, analogous to `public/catalogue/*`). Partitioned by
`area_id` then local `date`.
