import logging
import os
import tempfile
import zipfile

import cdsapi
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# Configure logging to show info on console
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)


def fetch_and_print_realtime():
    """
    Fetches the same data as ingestion.py but only prints the last 5 hours.
    Reinforces UTC time and avoids saving permanent files.
    Includes Open-Meteo for comparison.
    """
    # 1. Setup Environment and Dates
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Look for .env in the parent directory (src/)
    env_path = os.path.join(script_dir, "..", ".env")
    load_dotenv(env_path)

    # We fetch the last 7 days to ensure we hit the 'real-time' window of both APIs
    # (ERA5-Land often has a few days lag, while ENTSO-E is near real-time)
    # Using UTC explicitly
    now_utc = pd.Timestamp.now(tz="UTC")
    start_date_dt = now_utc - pd.Timedelta(days=7)

    start_date = start_date_dt.strftime("%Y-%m-%d")
    end_date = now_utc.strftime("%Y-%m-%d")

    logger.info(f"Verification Period: {start_date} to {end_date} (UTC)")

    # 2. ENTSO-E Load Data
    api_key = os.getenv("ENTSOE_API_KEY")
    if not api_key:
        logger.error(f"ENTSOE_API_KEY not found! Checked in: {env_path}")
    else:
        try:
            logger.info("Querying ENTSO-E for real-time load (ES)...")
            client = EntsoePandasClient(api_key=api_key)

            # Querying with UTC timestamps
            # Note: We query up to now_utc
            load_data = client.query_load("ES", start=start_date_dt, end=now_utc)

            # Ensure the index is UTC and sorted
            load_data.index = pd.to_datetime(load_data.index).tz_convert("UTC")
            load_data = load_data.sort_index()

            print("\n" + "=" * 80)
            print("ENTSO-E LOAD DATA (LAST 5 HOURS - UTC)")
            print("=" * 80)
            if not load_data.empty:
                print(load_data.tail(5))
                print(f"Latest timestamp: {load_data.index[-1]}")
            else:
                print("No data returned from ENTSO-E.")
        except Exception as e:
            logger.error(f"ENTSO-E Fetch Failed: {e}")

    # 3. Open-Meteo Data (New)
    try:
        logger.info("Querying Open-Meteo for real-time weather (Madrid)...")
        # Open-Meteo variables equivalent to ERA5
        open_meteo_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 40.4,
            "longitude": -3.7,
            "hourly": "temperature_2m,dew_point_2m,surface_pressure,precipitation,"
            + "shortwave_radiation,terrestrial_radiation,skin_temperature,"
            + "soil_temperature_0_to_7cm,soil_moisture_0_to_7cm,wind_speed_10m,"
            + "wind_direction_10m",
            "past_days": 7,
            "timezone": "UTC",
        }
        try:
            response = requests.get(open_meteo_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception:
            logger.error("error fetching open-meteo data")

        om_df = pd.DataFrame(data["hourly"])
        om_df["time"] = pd.to_datetime(om_df["time"], utc=True)

        # Calculate U and V components for wind
        # u = -speed * sin(dir), v = -speed * cos(dir) (Meteorological convention)
        rad = np.deg2rad(om_df["wind_direction_10m"])
        om_df["u10"] = -om_df["wind_speed_10m"] * np.sin(rad)
        om_df["v10"] = -om_df["wind_speed_10m"] * np.cos(rad)

        print("\n" + "=" * 80)
        print("OPEN-METEO WEATHER DATA (LAST 5 HOURS - UTC)")
        print("=" * 80)
        # Only show up to current time (Open-Meteo also provides forecasts)
        om_df_past = om_df[om_df["time"] <= now_utc]
        if not om_df_past.empty:
            print(om_df_past.tail(5)[["time", "temperature_2m", "u10", "v10", "shortwave_radiation"]])
            print(f"Latest timestamp: {om_df_past['time'].iloc[-1]}")
        else:
            print("No past data returned from Open-Meteo.")

    except Exception as e:
        logger.error(f"Open-Meteo Fetch Failed: {e}")

    # 4. Copernicus ERA5-Land Data
    try:
        logger.info("Querying Copernicus ERA5-Land for weather data (Madrid)...")
        c_client = cdsapi.Client()
        dataset = "reanalysis-era5-land-timeseries"

        request = {
            "variable": [
                "2m_dewpoint_temperature",
                "2m_temperature",
                "surface_pressure",
                "total_precipitation",
                "surface_solar_radiation_downwards",
                "surface_thermal_radiation_downwards",
                "skin_temperature",
                "soil_temperature_level_1",
                "volumetric_soil_water_level_1",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
            ],
            "location": {"longitude": -3.7, "latitude": 40.4},
            "date": [f"{start_date}/{end_date}"],
            "data_format": "csv",
        }

        # Using a temporary directory for the download to avoid cluttering raw data folders
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_zip = os.path.join(tmp_dir, "temp_weather.zip")
            logger.info("Downloading Copernicus data...")
            c_client.retrieve(dataset, request).download(temp_zip)

            with zipfile.ZipFile(temp_zip, "r") as z:
                csv_file = z.namelist()[0]
                with z.open(csv_file) as f:
                    weather_df = pd.read_csv(f)

            # Process timestamps to UTC
            time_col = "valid_time" if "valid_time" in weather_df.columns else "datetime"
            weather_df[time_col] = pd.to_datetime(weather_df[time_col], utc=True)
            weather_df = weather_df.sort_values(time_col)

            print("\n" + "=" * 80)
            print("COPERNICUS WEATHER DATA (LAST 5 HOURS - UTC)")
            print("=" * 80)
            if not weather_df.empty:
                # Print last 5 hours
                print(weather_df.tail(5))
                print(f"Latest timestamp: {weather_df[time_col].iloc[-1]}")
            else:
                print("No data returned from Copernicus.")

    except Exception as e:
        logger.error(f"Copernicus Fetch Failed: {e}")


if __name__ == "__main__":
    fetch_and_print_realtime()
