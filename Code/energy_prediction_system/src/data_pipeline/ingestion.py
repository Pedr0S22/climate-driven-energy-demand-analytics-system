import logging
import os
import time
import zipfile

# for copernicus
import cdsapi
import pandas as pd
import requests

# for gdrive
try:
    from data_pipeline.gdrive_sync import backup_project_data
except (ImportError, ModuleNotFoundError):
    from gdrive_sync import backup_project_data
from dotenv import load_dotenv

# for entsoe
from entsoe import EntsoePandasClient

MAX_RETRIES = 3


def fetch_copernicus_data(start_date: str, end_date: str):
    if pd.Timestamp(start_date) > pd.Timestamp(end_date):
        raise ValueError("start_date cannot be strictly after end_date.")

    logging.info(f"Fetching Copernicus ERA5-Land timeseries data from {start_date} to {end_date}...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

    raw_weather_dir = os.path.join(PROJECT_ROOT, "data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)

    dataset = "reanalysis-era5-land-timeseries"

    # Define paths for both the final CSV and the temporary ZIP
    output_csv_path = os.path.join(raw_weather_dir, f"era5_timeseries_{start_date}_to_{end_date}.csv")
    temp_zip_path = os.path.join(raw_weather_dir, f"era5_timeseries_{start_date}_to_{end_date}.zip")

    if os.path.exists(output_csv_path):
        logging.info(f"Skipping: File already exists: {output_csv_path}")
        return

    client = cdsapi.Client()

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

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Downloading Copernicus data (saving as ZIP)... [Attempt {attempt + 1}/{MAX_RETRIES}]")
            # Download to the temporary ZIP path instead of directly to CSV
            client.retrieve(dataset, request).download(temp_zip_path)

            logging.info("Extracting ZIP file...")
            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                # Get the name of the file inside the zip
                extracted_file_names = zip_ref.namelist()
                zip_ref.extractall(raw_weather_dir)

                # Rename the extracted file to match your desired output name
                if extracted_file_names:
                    extracted_file_path = os.path.join(raw_weather_dir, extracted_file_names[0])
                    if extracted_file_path != output_csv_path:
                        os.replace(extracted_file_path, output_csv_path)  # os.replace safely overwrites

            # Clean up the temporary zip file
            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)
            logging.info(f"Success: Saved and extracted Copernicus data to {output_csv_path}")
            break

        # Catch specifically if the file isn't a ZIP
        except zipfile.BadZipFile:
            logging.error("The downloaded file is not a valid ZIP archive. It might be an API error message.")
            with open(temp_zip_path, errors="ignore") as f:
                logging.error(f"Server Response snippet: {f.read()[:500]}")

            if attempt < MAX_RETRIES - 1:
                sleep_time = 2**attempt
                logging.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached for Copernicus API.")

        except Exception:
            logging.error("Failed to fetch Copernicus data.", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2**attempt
                logging.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached for Copernicus data fetch.")


def fetch_entsoe_data(start_date: str, end_date: str, country_code: str = "ES"):
    if pd.Timestamp(start_date) > pd.Timestamp(end_date):
        raise ValueError("start_date cannot be strictly after end_date.")

    logging.info(f"Fetching ENTSO-E load data for {country_code} from {start_date} to {end_date}...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    os.makedirs(raw_energy_dir, exist_ok=True)
    output_path = os.path.join(raw_energy_dir, f"entsoe_{country_code}_load_{start_date}_to_{end_date}.csv")

    if os.path.exists(output_path):
        logging.info(f"Skipping: File already exists: {output_path}")
        return

    env_path = os.path.join(SCRIPT_DIR, "..", ".env")
    load_dotenv(env_path)
    api_key = os.getenv("ENTSOE_API_KEY")

    if not api_key:
        logging.error(f"ENTSOE_API_KEY not found! Looked in: {env_path}")
        return

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Querying ENTSO-E API... [Attempt {attempt + 1}/{MAX_RETRIES}]")
            client = EntsoePandasClient(api_key=api_key)
            start = pd.Timestamp(start_date, tz="Europe/Madrid")
            end = pd.Timestamp(end_date, tz="Europe/Madrid") + pd.Timedelta(days=1)

            load_data = client.query_load(country_code, start=start, end=end)
            load_data.to_csv(output_path, header=["Load_MW"])
            logging.info(f"Success: Saved ENTSO-E data to {output_path}")
            break

        except Exception:
            logging.error("Failed to fetch ENTSO-E data.", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2**attempt
                logging.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached for ENTSO-E data fetch.")


def fetch_realtime_energy_load(days: int = 7, country_code: str = "ES"):
    """
    Fetches the latest Actual Total Load from ENTSO-E for the last N days.
    Saves to data/raw/energy/realtime_load.csv.
    """
    logging.info(f"Fetching real-time ENTSO-E load data for {country_code} (last {days} days)...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    os.makedirs(raw_energy_dir, exist_ok=True)
    output_path = os.path.join(raw_energy_dir, "realtime_load.csv")

    env_path = os.path.join(SCRIPT_DIR, "..", ".env")
    load_dotenv(env_path)
    api_key = os.getenv("ENTSOE_API_KEY")

    if not api_key:
        logging.error(f"ENTSOE_API_KEY not found! Looked in: {env_path}")
        return

    now_utc = pd.Timestamp.now(tz="UTC")
    start_date_dt = now_utc - pd.Timedelta(days=days)

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Querying ENTSO-E API... [Attempt {attempt + 1}/{MAX_RETRIES}]")
            client = EntsoePandasClient(api_key=api_key)

            # Querying with UTC timestamps
            load_data = client.query_load(country_code, start=start_date_dt, end=now_utc)

            if isinstance(load_data, pd.Series):
                load_data = load_data.to_frame(name="Load_MW")
            elif isinstance(load_data, pd.DataFrame):
                if "Actual Load" in load_data.columns:
                    load_data = load_data[["Actual Load"]].rename(columns={"Actual Load": "Load_MW"})
                else:
                    load_data.columns = ["Load_MW"]

            # Robust Save: Save to .tmp and rename only on success
            tmp_path = f"{output_path}.tmp"
            load_data.to_csv(tmp_path)
            os.replace(tmp_path, output_path)

            logging.info(f"Success: Saved real-time ENTSO-E data to {output_path}")
            break

        except Exception:
            logging.error("Failed to fetch real-time ENTSO-E data.", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2**attempt
                logging.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached for real-time ENTSO-E data fetch.")


def fetch_realtime_weather(days: int = 7, lat: float = 40.4, lon: float = -3.7):
    """
    Fetches the latest weather data from Open-Meteo for the last N days.
    Saves to data/raw/weather/realtime_weather.csv.
    Variables are mapped to match ERA5 schema names.
    """
    logging.info(f"Fetching real-time weather data from Open-Meteo (last {days} days)...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

    raw_weather_dir = os.path.join(PROJECT_ROOT, "data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)
    output_path = os.path.join(raw_weather_dir, "realtime_weather.csv")

    # Open-Meteo variables equivalent to ERA5
    open_meteo_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,dew_point_2m,surface_pressure,precipitation,shortwave_radiation,"
        "terrestrial_radiation,skin_temperature,soil_temperature_0_to_7cm,"
        "soil_moisture_0_to_7cm,wind_speed_10m,wind_direction_10m",
        "past_days": days,
        "timezone": "UTC",
    }

    for attempt in range(MAX_RETRIES):
        try:
            logging.info(f"Querying Open-Meteo API... [Attempt {attempt + 1}/{MAX_RETRIES}]")
            response = requests.get(open_meteo_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            om_df = pd.DataFrame(data["hourly"])

            # Map Open-Meteo names to ERA5 schema names
            mapping = {
                "time": "datetime",
                "temperature_2m": "t2m",
                "dew_point_2m": "d2m",
                "surface_pressure": "sp",
                "precipitation": "tp",
                "shortwave_radiation": "ssrd",
                "terrestrial_radiation": "strd",
                "skin_temperature": "skt",
                "soil_temperature_0_to_7cm": "stl1",
                "soil_moisture_0_to_7cm": "swvl1",
            }
            om_df = om_df.rename(columns=mapping)

            # ERA5 also has latitude and longitude in the CSV
            om_df["latitude"] = lat
            om_df["longitude"] = lon

            # Robust Save: Save to .tmp and rename only on success
            tmp_path = f"{output_path}.tmp"
            om_df.to_csv(tmp_path, index=False)
            os.replace(tmp_path, output_path)

            logging.info(f"Success: Saved real-time weather data to {output_path}")
            break

        except Exception:
            logging.error("Failed to fetch real-time weather data.", exc_info=True)
            if attempt < MAX_RETRIES - 1:
                sleep_time = 2**attempt
                logging.warning(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached for Open-Meteo data fetch.")


def data_retrieval(start_date: str, end_date: str, country_code: str = "ES"):
    """Master function to orchestrate data ingestion from multiple sources and backup."""
    fetch_entsoe_data(start_date, end_date, country_code)
    fetch_copernicus_data(start_date, end_date)
    backup_project_data()


def realtime_data_retrieval(days: int = 7, country_code: str = "ES"):
    """Master function to orchestrate real-time data ingestion and backup."""
    fetch_realtime_energy_load(days, country_code)
    fetch_realtime_weather(days)
    backup_project_data()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    start_date = "2020-01-01"
    end_date = "2025-12-31"

    start_time = time.time()
    data_retrieval(start_date, end_date, country_code="ES")
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Total execution time of Ingestion Module: {elapsed_time:.2f} seconds")
