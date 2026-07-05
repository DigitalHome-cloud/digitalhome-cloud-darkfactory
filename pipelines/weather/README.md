# Area weather data lake

Hourly weather per **Area** (`{country}-{postalCode}`, e.g. `DE-39576`), stored
as a Delta Lake table. Weather is keyed by area, never by SmartHome — many homes
share one area, and a `DigitalHome` already carries `country`+`postalCode`.

Reference stack (matches `../../experimental/data`): delta-rs (`deltalake==1.5.1`) + pandas +
pyarrow. Provider: **Open-Meteo** historical archive (ERA5) — free, no API key.

## Layout
- `config.py` — variables, table path (`WEATHER_LAKE` env, local by default)
- `areas.json` — the 3 seed areas + centroid lat/lon + timezone
- `fetch_openmeteo.py` — one area, one date-range → tidy DataFrame
- `weather_ingest.py` — write to the bronze Delta table (idempotent per area/range)
- `backfill.py` — one-time historical load, chunked by year
- `read_weather.py` — summary + sample filtered read
- `manifest.json` — column → Brick class + QUDT unit

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
