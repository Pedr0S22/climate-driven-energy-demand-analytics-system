# for copernicus
import os
import cdsapi

# for entso/e
import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

# for gdrive
from gdrive_sync import backup_project_data


def fetch_copernicus_data(start_date: str, end_date: str):
    print(f"Fetching Copernicus ERA5-Land timeseries data from {start_date} to {end_date}...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

    raw_weather_dir = os.path.join(PROJECT_ROOT, "data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)

    dataset = "reanalysis-era5-land-timeseries"
    client = cdsapi.Client()

    output_path = os.path.join(raw_weather_dir, f"era5_timeseries_{start_date}_to_{end_date}.csv")

    if os.path.exists(output_path):
        print(f"    [Skipping] File already exists: {output_path}")
        return

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
            "10m_v_component_of_wind"
        ],
        "location": {"longitude": -3.7, "latitude": 40.4},
        "date": [f"{start_date}/{end_date}"],
        "data_format": "csv"
    }

    try:
        print(f"    -> Downloading Copernicus data...")
        client.retrieve(dataset, request).download(output_path)
        print(f"    [Success] Saved Copernicus data to {output_path}")
    except Exception as e:
        print(f"    [Error] Failed to fetch Copernicus data: {e}")


def fetch_entsoe_data(start_date: str, end_date: str, country_code: str = "ES"):
    print(f"\nFetching ENTSO-E load data for {country_code} from {start_date} to {end_date}...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    os.makedirs(raw_energy_dir, exist_ok=True)
    output_path = os.path.join(raw_energy_dir, f"entsoe_{country_code}_load_{start_date}_to_{end_date}.csv")

    if os.path.exists(output_path):
        print(f"    [Skipping] File already exists: {output_path}")
        return

    env_path = os.path.join(SCRIPT_DIR, ".env")
    load_dotenv(env_path)
    api_key = os.getenv("ENTSOE_API_KEY")

    if not api_key:
        print(f"    [Error] ENTSOE_API_KEY not found! Looked in: {env_path}")
        return
    try:
        client = EntsoePandasClient(api_key=api_key)
        start = pd.Timestamp(start_date, tz="Europe/Madrid")
        end = pd.Timestamp(end_date, tz="Europe/Madrid") + pd.Timedelta(days=1)

        load_data = client.query_load(country_code, start=start, end=end)
        load_data.to_csv(output_path, header=["Load_MW"])
        print(f"    [Success] Saved ENTSO-E data to {output_path}")

    except Exception as e:
        print(f"    [Error] Failed to fetch ENTSO-E data: {e}")


if __name__ == "__main__":
    start_date = "2020-01-01"
    end_date = "2025-12-31"

    # Fetch the entire timeseries for both ENTSO-E and Copernicus in one go
    fetch_entsoe_data(start_date, end_date, country_code="ES")
    fetch_copernicus_data(start_date, end_date)

    #backup_project_data()
