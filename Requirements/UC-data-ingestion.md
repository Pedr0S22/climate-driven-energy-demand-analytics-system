# UC1: Data Ingestion

**Primary Actor:** Data Scientist / Developer


**Scope/Goal:** The data ingestion layer of the Climate-Driven Energy Demand Analytics System.The goal is to retrieve electricity demand data from "ENTSO-E" dataset found at [https://transparency.entsoe.eu/]  and climate data from "ERA5
Land Hourly data from 1950 to present" dataset found at [https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview]. The ingestion process must be reproducible and executable through code, not manual steps.

**Level:** User Goal

**Stakeholders and Interests:**

* **Client:** Needs the system to securely ingest real-world data from stable, publicly available international datasets to explore how climate affects electricity demand.
* **Developer / Data Scientist:** Needs to execute the data ingestion script reliably, ensure raw data is stored in a dedicated raw-data directory without manual modification.
* **Security Administrator:** Needs absolute certainty that no credentials or API keys are hardcoded in the repository and that configuration files such as `.env` are excluded from version control.

**Preconditions:**

1. API credentials for ENTSO-E and Copernicus are securely configured using environment variables.
2. The system must be configured to target one selected European country and a timeframe of at least one full year.


**Main Success Scenario:**

1. The Developer / Data Scientist executes the data ingestion script via the command line.
2. The system begins measuring the execution time for the data ingestion component.
3. The system connects to the ENTSO-E Transparency Platform and retrieves at least one full year of hourly electricity load data. The primary target variable retrieved is total electricity load, expressed in megawatts (MW)
4. The system connects to the Copernicus Climate Data Store (ERA5 dataset) and retrieves meteorological data. Specifically, it extracts:
* 2-meter air temperature (in Kelvin)
* solar radiation (in J/m²)
* 10-meter wind speed (in m/s)
* Total precipitation (in m)
5. The system stores the unmodified raw climate data into the `/data/raw/weather/` directory.
6. The system stores the unmodified raw electricity data into the `/data/raw/energy/` directory.
7. The system successfully logs the execution time so it can be summarized in the project documentation.

**Extensions:**

3. a) API connection failure or authentication error with ENTSO-E:

    * 3a1. The system detects that the ENTSO-E Transparency Platform is unreachable or authentication fails.

    * 3a2. The system properly logs the ingestion failure.

    * 3a3. The system results in a clean termination of the ingestion script.

3. b) Missing or incomplete data returned from ENTSO-E:

    * 3b1. The ENTSO-E API returns gaps, timeouts, or missing records for the requested period.

    * 3b2. The system handles the failure gracefully.

    * 3b3. The system ensures the missing data does not cause an uncontrolled crash.

    * 3b4. The system logs the anomaly and terminates cleanly.

4. a) API connection failure or authentication error with Copernicus:

    * 4a1. The system detects that the Copernicus Climate Data Store is unreachable or authentication fails.

    * 4a2. The system properly logs the ingestion failure.

    * 4a3. The system results in a clean termination of the ingestion script.

4. b) Missing or incomplete data returned from Copernicus:

    * 4b1. The Copernicus API returns gaps or missing meteorological records.

    * 4b2. The system handles the failure gracefully.

    * 4b3. The system ensures the missing data does not cause an uncontrolled crash.

    * 4b4. The system logs the anomaly and terminates cleanly.