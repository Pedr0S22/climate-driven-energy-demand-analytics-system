import os
import cdsapi

def fetch_copernicus_data(year: str):
    print(f"Fetching Copernicus ERA5-Land data for {year}...")
    
    raw_weather_dir = os.path.join("data", "raw", "weather")
    os.makedirs(raw_weather_dir, exist_ok=True)
    
    dataset = "reanalysis-era5-land"
    client = cdsapi.Client()

    # We will loop through months 01 to 12 to avoid the "Request too large" error
    months = [f"{i:02d}" for i in range(1, 13)]
    
    for month in months:
        print(f" -> Downloading data for {year}-{month}...")
        
        # Save each month as its own file
        output_path = os.path.join(raw_weather_dir, f"era5_climate_{year}_{month}.nc")
        
        # If the file already exists, skip downloading it again
        if os.path.exists(output_path):
            print(f"    [Skipping] File already exists: {output_path}")
            continue
            
        request = {
            "variable": [
                "2m_dewpoint_temperature",
                "2m_temperature",
                "soil_temperature_level_1",
                "lake_total_layer_temperature",
                "surface_net_solar_radiation",
                "surface_sensible_heat_flux",
                "total_evaporation",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "surface_pressure",
                "total_precipitation"
            ],
            "year": year,
            "month": month,  # Requesting ONE month at a time
            "day": [f"{i:02d}" for i in range(1, 32)],
            "time": [f"{i:02d}:00" for i in range(24)],
            "area": [42.15, -9.5, 36.96, -6.19], # Portuguese bounding box
            "data_format": "netcdf",
            "download_format": "unarchived"
        }

        try:
            client.retrieve(dataset, request, output_path)
            print(f"    [Success] Saved Copernicus data to {output_path}")
        except Exception as e:
            # Ingestion failures must be properly logged [cite: 89]
            print(f"    [Error] Failed to fetch Copernicus data for {month}: {e}")

if __name__ == "__main__":
    fetch_copernicus_data("2024")