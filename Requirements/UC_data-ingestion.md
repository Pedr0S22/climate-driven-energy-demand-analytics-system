# UC1: Data Ingestion

**Primary Actor:** System (Automated Pipeline)

**Scope/Goal:** The data ingestion layer of the Climate-Driven Energy Demand Analytics System.The goal is to retrieve electricity demand data from ENTSO-E and climate data from ERA5. The ingestion process must be reproducible and executable through code, not manual steps.

**Level:** Subfunction / System Goal

**Stakeholders and Interests:**

* **Developer / Data Scientist:** Needs the system to retrieve data automatically and ensure that raw data is stored in a dedicated raw-data directory without manual modification.
* **Security Administrator:** Needs assurance that no credentials or API keys may be hardcoded in the repository.

**Preconditions:**

1. Environment variables must be used where necessary for API authentication.
2. Configuration files such as .env must be excluded from version control.
3. The system must be configured to target one selected European country and a timeframe of at least one full year.


**Main Success Scenario:**

1. The system initiates the automated data ingestion script via code.
2. The system begins to measure the execution time for the data ingestion process.
3. The system connects to the ENTSO-E Transparency Platform and retrieves at least one full year of hourly electricity load data. The primary target variable retrieved is total electricity load, expressed in megawatts.
4. The system connects to the Copernicus Climate Data Store and retrieves the ERA5 dataset for the same country, or for a representative city within that country.
5. The system successfully requests hourly resolution data for 2-meter air temperature, solar radiation, and 10-meter wind speed.
6. The system stores the raw climate datasets into the `/data/raw/weather/` directory.
7. The system stores the raw electricity datasets into the `/data/raw/energy/` directory.
8. The system logs the execution times for the ingestion process so they can be summarized in the project documentation.

**Extensions:**

* **3. a) / 4. a) API Connection Failure or Timeout:**
    * 3a1. The system detects that the ENTSO-E or Copernicus API is unreachable or times out.
    * 3a2. The system ensures ingestion failures must be properly logged and result in a clean termination.
* **3. b) / 4. b) Missing or Incomplete Data from API:**
    * 3b1. The external dataset returns gaps or missing timestamps for the requested period.
    * 3b2. The system must handle failures gracefully.
    * 3b3. The system ensures that missing data must not cause uncontrolled crashes.