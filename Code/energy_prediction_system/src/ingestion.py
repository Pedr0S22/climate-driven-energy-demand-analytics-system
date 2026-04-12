# for copernicus
import logging
import os
import time
import zipfile

import cdsapi

# for entso/e
import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# for gdrive
from gdrive_sync import backup_project_data

MAX_RETRIES = 3


def fetch_copernicus_data(start_date: str, end_date: str):
    if pd.Timestamp(start_date) > pd.Timestamp(end_date):
        raise ValueError("start_date cannot be strictly after end_date.")

    logging.info(f"Fetching Copernicus ERA5-Land timeseries data from {start_date} to {end_date}...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

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
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    os.makedirs(raw_energy_dir, exist_ok=True)
    output_path = os.path.join(raw_energy_dir, f"entsoe_{country_code}_load_{start_date}_to_{end_date}.csv")

    if os.path.exists(output_path):
        logging.info(f"Skipping: File already exists: {output_path}")
        return

    env_path = os.path.join(SCRIPT_DIR, ".env")
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


def data_retrieval(start_date: str, end_date: str, country_code: str = "ES"):
    """Master function to orchestrate data ingestion from multiple sources and backup."""
    fetch_entsoe_data(start_date, end_date, country_code)
    fetch_copernicus_data(start_date, end_date)
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
