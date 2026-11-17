"""Solar position (sun angle in the sky) for PV/solar planning.

Uses pvlib's NREL solar-position algorithm. Given UTC timestamps and an area's
lat/lon, returns solar elevation, azimuth, and zenith — the geometry you need to
choose panel tilt/orientation and estimate plane-of-array irradiance.
"""
import pandas as pd
import pvlib

from config import SOLAR_POSITION_COLS


def sun_position(times_utc, latitude, longitude):
    """times_utc: tz-aware UTC DatetimeIndex/Series. Returns a DataFrame with
    solar_elevation, solar_azimuth, solar_zenith (degrees), aligned to input."""
    idx = pd.DatetimeIndex(pd.to_datetime(times_utc, utc=True))
    sp = pvlib.solarposition.get_solarposition(idx, latitude, longitude)
    out = pd.DataFrame(
        {
            "solar_elevation": sp["apparent_elevation"].to_numpy(),
            "solar_azimuth": sp["azimuth"].to_numpy(),
            "solar_zenith": sp["apparent_zenith"].to_numpy(),
        }
    )
    return out[SOLAR_POSITION_COLS].round(3)


if __name__ == "__main__":
    t = pd.date_range("2024-06-21 09:00", "2024-06-21 13:00", freq="1h", tz="UTC")
    print(sun_position(t, 52.6061, 11.8585).to_string())
