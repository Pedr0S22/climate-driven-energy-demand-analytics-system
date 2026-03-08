# for copernicus
import os
import calendar
import cdsapi
#for entso/e
import pandas as pd
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

def fetch_copernicus_data(year: str):
    print(f"Fetching Copernicus ERA5-Land data for {year}...")
    raw_weather_dir = os.path.join("data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)
    dataset = "reanalysis-era5-land"
    client = cdsapi.Client()

    variables = [
        "2m_dewpoint_temperature",
        "2m_temperature"
        "soil_temperature_level_1",
        "lake_total_layer_temperature",
        "surface_net_solar_radiation",
        "surface_sensible_heat_flux",
        "total_evaporation",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_pressure",
        "total_precipitation"
    ]

    # Loop through each month
    for month in range(1, 13):
        month_str = f"{month:02d}"
        
        # Get the exact number of days in this specific month/year
        _, num_days = calendar.monthrange(int(year), month)
        valid_days = [f"{d:02d}" for d in range(1, num_days + 1)]
        
        # Loop through each variable individually
        for var in variables:
            print(f" -> Downloading {var} for {year}-{month_str}...")
            output_path = os.path.join(raw_weather_dir, f"era5_{year}_{month_str}_{var}.nc")
            
            # Skip if already downloaded
            if os.path.exists(output_path):
                print(f"    [Skipping] File already exists: {output_path}")
                continue
                
            request = {
                "variable": [var], # Asking for just ONE variable at a time
                "year": year,
                "month": month_str,
                "day": valid_days, # Only valid days for this month
                "time": [f"{i:02d}:00" for i in range(24)],
                "area": [43.79, -9.30, 36.00, 3.33], # Spain bounding box
                "data_format": "netcdf",
                "download_format": "unarchived"
            }

            try:
                client.retrieve(dataset, request, output_path)
                print(f"    [Success] Saved to {output_path}")
            except Exception as e:
                print(f"    [Error] Failed to fetch {var} for {month_str}: {e}")


def fetch_entsoe_data(year: str, country_code: str = 'ES'):
    print(f"\nFetching ENTSO-E load data for {country_code} in {year}...")
    
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
    raw_energy_dir = os.path.join(PROJECT_ROOT, "data", "raw", "energy")
    os.makedirs(raw_energy_dir, exist_ok=True)
    
    output_path = os.path.join(raw_energy_dir, f"entsoe_{country_code}_load_{year}.csv")
    
    # Skip if already downloaded
    if os.path.exists(output_path):
        print(f"    [Skipping] File already exists: {output_path}")
        return

    # load API Key from .env
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    api_key = os.getenv("ENTSOE_API_KEY")
    
    if not api_key:
        print("    [Error] ENTSOE_API_KEY not found in .env file! Please add it.")
        return

    try:
        client = EntsoePandasClient(api_key=api_key)
        start = pd.Timestamp(f"{year}-01-01", tz='Europe/Madrid')
        end = pd.Timestamp(f"{int(year)+1}-01-01", tz='Europe/Madrid')
        
        load_data = client.query_load(country_code, start=start, end=end)
        load_data.to_csv(output_path, header=["Load_MW"])
        print(f"    [Success] Saved ENTSO-E data to {output_path}")
        
    except Exception as e:
        print(f"    [Error] Failed to fetch ENTSO-E data: {e}")

if __name__ == "__main__":
    targetyear = "2024"
    fetch_entsoe_data(targetyear , country_code='ES')
    fetch_copernicus_data(targetyear)