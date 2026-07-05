"""Shared config for the area weather + air-quality data lake.

Matches the experimental/data reference stack: delta-rs (deltalake==1.5.1) +
pandas + pyarrow, Hive-partitioned Delta tables. Everything is keyed by AREA
({country}-{postalCode}); a SmartHome links to its area, never the reverse.

Times are stored in **UTC** (canonical; sun position needs UTC and it dodges
DST-localization bugs). Solar-siting variables (irradiance components + computed
sun elevation/azimuth) support PV panel and wind-turbine planning.
"""
import os

# ── Open-Meteo endpoints (free, no API key) ───────────────────────────────────
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"        # ERA5, 1940+
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"  # CAMS, 2013+

# Deep-history start for each product (air quality only reaches back to 2013).
WEATHER_START = "2000-01-01"
AIR_QUALITY_START = "2013-01-01"

# ── Weather hourly variables (ERA5) ───────────────────────────────────────────
# Core meteorology + solar-resource (irradiance components) + wind at 10m & 100m
# (turbine hub height). Sun elevation/azimuth/zenith are COMPUTED (see solar.py),
# not fetched.
HOURLY_VARS = [
    # thermodynamics
    "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
    # precipitation
    "precipitation", "rain", "snowfall",
    # pressure / cloud
    "pressure_msl", "surface_pressure", "cloud_cover",
    # wind (10 m + 100 m hub height + gusts)
    "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
    "wind_speed_100m", "wind_direction_100m",
    # solar resource: GHI, DNI, DHI, top-of-atmosphere, sunshine, day flag
    "shortwave_radiation", "direct_normal_irradiance", "diffuse_radiation",
    "terrestrial_radiation", "sunshine_duration", "is_day",
    # evapotranspiration
    "et0_fao_evapotranspiration",
]
# Computed by solar.py from (lat, lon, UTC time):
SOLAR_POSITION_COLS = ["solar_elevation", "solar_azimuth", "solar_zenith"]

# ── Air-quality hourly variables (CAMS reanalysis) ────────────────────────────
AIR_QUALITY_VARS = [
    "pm10", "pm2_5", "nitrogen_dioxide", "ozone", "sulphur_dioxide",
    "carbon_monoxide", "dust", "aerosol_optical_depth", "uv_index",
]

# ── Lake layout ───────────────────────────────────────────────────────────────
# Local by default (no creds for the backfill); WEATHER_LAKE=s3://<bucket>/public/weather
LAKE_ROOT = os.environ.get(
    "WEATHER_LAKE",
    os.path.join(os.path.dirname(__file__), "lake"),
)
# Bronze tables, partitioned by area then YEAR (year-sized files pack ~8760
# rows each — good compression + pruning). `date` stays a column for filtering.
OBSERVATIONS_TABLE = f"{LAKE_ROOT.rstrip('/')}/observations"    # weather
AIR_QUALITY_TABLE = f"{LAKE_ROOT.rstrip('/')}/air_quality"      # pollution
PARTITION_BY = ["area_id", "year"]

AREAS_FILE = os.path.join(os.path.dirname(__file__), "areas.json")
