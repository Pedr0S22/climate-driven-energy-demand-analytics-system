import os
import calendar
import cdsapi

def fetch_copernicus_data(year: str):
    print(f"Fetching Copernicus ERA5-Land data for {year}...")
    raw_weather_dir = os.path.join("data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)
    dataset = "reanalysis-era5-land"
    client = cdsapi.Client()

    # The exact list of variables
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

    # 1. Loop through each month
    for month in range(1, 13):
        month_str = f"{month:02d}"
        
        # Get the exact number of days in this specific month/year (fixes the February 30th bug!)
        _, num_days = calendar.monthrange(int(year), month)
        valid_days = [f"{d:02d}" for d in range(1, num_days + 1)]
        
        # 2. CRITICAL FIX: Loop through each variable individually
        for var in variables:
            print(f" -> Downloading {var} for {year}-{month_str}...")
            
            # Save file as: era5_2024_01_2m_temperature.nc
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
                "data_format": "netcdf", # If this fails, change to "netcdf4" based on your screenshot!
                "download_format": "unarchived"
            }

            try:
                client.retrieve(dataset, request, output_path)
                print(f"    [Success] Saved to {output_path}")
            except Exception as e:
                print(f"    [Error] Failed to fetch {var} for {month_str}: {e}")

if __name__ == "__main__":
    fetch_copernicus_data("2024")