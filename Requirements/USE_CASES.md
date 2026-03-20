# USE CASE DEFINITIONS - V1.1

This file contains all UCs for the development of this project.

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
3. The system connects to the ENTSO-E Transparency Platform and retrives the primary target variable which is total electricity load, expressed in megawatts (MW)
4. The system connects to the Copernicus Climate Data Store (ERA5 dataset) and retrieves meteorological data. Specifically, it extracts:

**For further familirization and better explanation regarding the variables mentioend below proceed to the Copernicus Climate Data Store**

* Lake total layer temperature (in Kelvin)
* 2-meter air temperature (in Kelvin)
* 2-meter dewpoint temperature (in Kelvin)
* soil temperature level1 (in kelvin)
* Surface solar radiation downwards (in J/m²)
* Surface latent heat flux (in J/m²)
* Surface pressure (in Pa)
* Total evaporation (m of water equivalent )
* 10-meter wind speed (both Eastward and Northward) (in m/s)
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

# UC2: Data Cleaning and Alignment

**Primary Actor:** Developer

**Scope/goal:** The objective is to clean, validate, align, and standardize the datasets to a common temporal resolution, ensuring data integrity, robustness, and quality before the training phase. The processed data must be stored in `/data/processed/`.

**Level:** User goals

**Stakeholders/Interests:**
- User: Wants to ensure the system uses clean and consistent data to generate reliable forecasts.
- Developer/ Data Analyst: Require reliable and consistent data to ensure robustness in the models and subsequent steps.
- Administrador: Needs assurance that raw data remains untouched and that processed data is stored separately under `/data/processed/`.

**Preconditions:**
- Data must be located in the correct folders from the previous step;
- The `/data/processed/` folder must exist;
- Datasets must contain the mandatory columns required for this process (timestamp, electricity load, temperature, solar radiation, wind speed, precipitation).


**Main Success Scenario:**
1. The use case begins when the data preprocessing module is executed.
2. The system loads raw data from `/data/raw/weather/` and `/data/raw/energy/`.
3. The system converts timestamps to the UTC standard and checks for any timezone inconsistencies.
4. The system handles missing values in the following variables: temperature, wind speed, solar radiation, electricity load, and precipitation.
5. The system detects outliers using the IQR method for all variables except electricity load. For each detected value, the system verifies whether it is plausible according to the predefined limits.
6. The system aggregates data every hour, averaging temperature, wind, radiation, and precipitation; for electrical charge, we use the maximum value for that interval.
7. The system merges both datasets into a single dataset and saves the processed data in the `/data/processed/` folder.

**Extensions:**

3. a) The system detects that not all expected timestamps (15-minute intervals) exist:
    * There is a missing time value; what we do is, since the data is for 15 minutes, we add a line for the timestamp that was supposed to be there, and the remaining variables are marked as missing values ​​for later processing.

4. a) Missing Values Detected
    1.  There is 1 isolated missing value per hour:
        - The system applies linear interpolation between the previous and the next value.
    2. There is more than 1 missing value within a 1-hour interval:
        - The system estimates missing values using statistical methods based on nearby valid observations.
        - For solar radiation, the system considers whether the timestamp corresponds to daytime or nighttime when estimating the value.
        - For precipitation, the system evaluates surrounding observations to determine whether the value should remain zero or be estimated from nearby valid data.

5. a) Outlier detected by IQR
    1. The value is outside the limits:
        - The system replaces the value using statistical estimates based on nearby valid observations, taking into account the characteristics of each variable;
    2. The value is outside the IQR but within plausible limits:
        - The system retains the value, considering it a possible outlier.
    
6. a) The timestamps are not all the same time:
    * There exists timestamps that do not exactly match xx:00, xx:15, xx:30, or xx:45:
        - The system adjusts them to the nearest 15-minute interval before time aggregation.
    
# UC3: Feature Engeneering

**Primary actor**:
Data Scientist/Developer

**Scope/Goal**:
Transform the clean and sincronized data into relevant predictive features (temporal, lagging, rolling, and advanced) to feed the modeling component, from which:


* **Mandatorty**:
    - **Temporal features**: hour, day, season;
    - At least one **rolling climate feature**;
    - At least one **lagged demand feature**.


* **Optional**:
    - Derived features.

**Level**:
User goal.

**Stakeholders and Interests**:

* **Data cientist**: Expects to obtain relevant features that capture trends, seasonality, and complex climate-energy relationships to improve model performance.

* **Data Engineer**: Expects an efficient, modular transformation process that is well-integrated into the system's pipeline.

* **Validator**: Aims to ensure that errors such as data leakage do not occur and that temporal integrity is maintained.

**Preconditions**:
1. The Data Cleaning and Alignment stage has been successfully completed.

2. Synchronized data is available in the `/data/processed/ `directory.

3. The system has validated that all required columns and timestamps are present and reliable.

**Main Success Scenario**:
1. The use case starts when the feature engineering module is activated, which occurs once the data cleaning stage is completed;

2. The system loads the data available in the `/data/processed/` directory;

3. The system extracts temporal features, including hour of the day, day of the week, and seasonal indicators.

4. The developer defines the window size and the overlap, constrained by the dataset timestamps, to ensure the rolling windows are physically meaningful;

5. The system extracts rolling climate features, such as:
    - mean;
    - median;
    - standard deviation;
    - variance;
    - root mean square;
    - average derivatives;
    - skewness, kurtosis, IQR, zero crossing rate, mean crossing rate, and pairwise correlation;

6. The system extracts lagged demand features, such as:
    - L1 Load: Electrical load one hour ago;
    - L24 Load: Load one day ago;
    - L168 Load: Load one week ago;

7. The system derives new features from the data to provide additional analytical depth, such as:
    - Temperature Anomalies: Deviation from seasonal/monthly means;
    - Climatic Indicators: Heating Degree Days (HDD) or Cooling Degree Days (CDD);
    - Heatwave/Coldwave Flags: Binary indicators based on persistent extreme temperatures.

8. The system validates that the features obtained don't include invalid values generated during the feature extraction process.

9. The system measures and logs the execution time.

10. The system logs the total feature count.

11. The system saves the full feature set as the primary dataset for the predictive model, ensuring the output format is compatible with the model training pipeline.

**Extensions**:

8. a) Minor domain inconsistencies detected (e.g., a few records with values that do not align with physical constraints):
    * 8a1. The system handles them by dropping or imputing the affected rows to maintain dataset quality.

    b) Critical domain-context errors detected (e.g., widespread anomalies where feature values are physically implausible):
    * 8b1. The system logs a domain consistency error and the process terminates to prevent training a model on nonsensical data.

    * 8b2. The developer must review the previous extraction logic or source data to identify the source of the contextual mistake.

10) a) High dimensionality detected:

    * 10a1. The system performs feature selection (e.g., Fisher Score, ReliefF) to identify the most predictive variables.

    * 10a2. The system performs dimensionality reduction (e.g., PCA) to compress information.

    * 10a3. The system generates and labels these new dataset versions.

    * 10a4. The system saves each resulting dataset version as a separate file to allow for comparative training and evaluation in the next stage.

    * 10a4. The system ensures these new versions are compatible with the model training pipeline.



# UC4: Modeling & Evaluation

**Primary Actor:** Data Scientist with Admin privileges

**Scope/Goal:** Use the optimized and reduced datasets from the Feature Engineering module to train regression models, evaluate their statistical performance, and select the best version for production through a temporal splitting strategy.

**Level:** User Goal Level (Sea Level)

**Stakeholders and Interests**

* **Administrator:** Requires a protected interface to trigger training and compare different data variants.
* **Project Supervisor:** Demands the application of rigorous metrics ($R^{2}$, MAE, RMSE) and the absolute prohibition of shuffling in time-series data.

**Preconditions**
1.  **Authentication:** The Administrator is authenticated in the system.
2.  **Feature Engineering Success:** Datasets with different reduction techniques are available in the `/data/processed/` directory.
3.  **Data History:** Availability of a x-year data history to allow for the x-x-x split.

**Main Success Scenario**
1.  The authenticated Administrator triggers the modeling pipeline.
2.  The system loads the processed electricity load and climate data from the `/data/processed/` directory.
3.  The system applies a **temporal train/test split** to maintain the chronological order of the data; 
4.  For both **Daily** and **Hourly** resolutions, the system executes the training for:
    * **Linear Regression** 
    * **Random Forest** 
5.  The system calculates mandatory performance metrics ($MAE$, $RMSE$, and $R^{2}$) for each model at each resolution. **Additional metrics may be computed as needed for further diagnostic purposes.**
6.  The system performs **residual analysis** to identify potential overfitting.
7.  The system automatically selects the best-performing models (one for daily and one for hourly) based on the validation metrics.
8.  The system persists the winning models and logs the training event, including the username and a timestamp.


**Extensions:**

* **1a. User without Administrator privileges:**
    * 1a1. The system denies access to the training functionality and logs the attempt.
* **2a. Inconsistency in data within `/data/processed/`:**
    * 2a1. The system detects a failure in the presence of mandatory columns.
    * 2a2. The system terminates the process gracefully, reporting the error in the log.
* **7a. Failure in statistical tests (e.g., insufficient variance):**
    * 7a1. The system uses the $R^{2}$ metric as a tie-breaker and notifies the Administrator in the report.



# UC5: Prediction Generation

**Primary Actor:** Authenticated User

**Scope/Goal:** Allow the user to obtain electricity demand predictions (in MW) for a specific period (day or hour) using trained models, accompanied by graphical visualizations and future projections.

**Level:** User Goal Level (Sea Level)

**Stakeholders and Interests:**

* **User:** Seeks fast, accurate predictions to plan consumption or analyze trends.
* **System Administrator:** Ensures only registered and authenticated users access prediction functionality.

**Preconditions:**
1.  **Authentication:** The user must be successfully authenticated in the system.
2.  **Model Availability:** Two distinct sets of models must be trained and persisted: one optimized for **daily** evaluation and another for **hourly** evaluation.
3.  **Data Infrastructure:** The `/data/processed/` directory must contain the necessary climate and energy features to support lag and rolling calculations.

**Main Success Scenario:**

#### Scenario A: Daily Prediction
1.  The authenticated user provides a specific date (e.g., `YYYY-MM-DD`).
2.  The system validates the input and retrieves the corresponding meteorological features.
3.  The system utilizes the **daily-optimized model** to calculate the demand.
4.  **Visualization:** The system displays a visual indicator with the specific daily prediction.
5.  **Future Projection:** The system automatically generates a forecast for the next $X$ days.

#### Scenario B: Hourly and Daily Prediction
1.  The authenticated user provides a specific date and hour (e.g., `YYYY-MM-DD HH:00`).
2.  The system validates the input format.
3.  The system utilizes the **hourly-optimized model** to generate a point prediction in Megawatts (MW).
4.  **Visualization:** The system displays a visual indicator with the specific hourly prediction.
5.  **Future Projection:** The system generates hourly predictions for the next $X$ consecutive hours.


6.  The system logs the action, including the username, timestamp, and input parameters.
7.  The result is delivered to the user in under 1 second.

**Extensions:**

* **1a. Unauthenticated User:**
    * 1a1. The system denies access to the prediction interface.
    * 1a2. The system logs the unauthorized attempt.
* **2a. Missing Data:**
    * 2a1. The system identifies the missing input and notifies the user that the prediction cannot be generated.
    * 2a2. The system terminates the process gracefully without exposing internal implementation details.
* **3a. Input Validation Failure:**
    * 3a1. The system detects an incorrect date format or invalid characters.
    * 3a2. The system returns a clear error message and prompts for corrected input.


# UC6: User Registration

**Primary Actor:** User

**Scope/Goal:** The user management module of the Climate-Driven Energy Demand Analytics System. The goal is to allow new users to register an account with a username, email and password so they can later authenticate and access the system's protected capabilities.

**Level:** User Goal

**Stakeholders and Interests:**

* **Unregistered User:** Needs a straightforward way to create an account to access prediction (user accounts).

* **Security Administrator:** Needs assurance that the chosen password enforces a minimum length of eight characters and maximum of twenty characters; is never stored in plaintext and is securely hashed using an appropriate cryptographic hash function before being saved.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user does not currently have an account with the required email

3. The user is not logged into the system.

**Main Success Scenario:**

1. The user accesses the registration section of the application.

2. The system prompts the user to provide a desired username, email and a password.

3. The user inputs a username, email and a password.

4. The system performs input validation to ensure the password meets the length requirements and to prevent trivial misuse.

5. The system verifies that the provided email is not already taken in the database.

6. The system securely hashes the password using an appropriate cryptographic hash function.

7. The system stores the new email, username, and the hashed password in the database.

8. The system logs the successful account creation, recording the timestamp and the new user's email and username.

9. The system informs the user of a successful registration and redirects them to the authentication/login flow.

**Extensions:**

4. a) Invalid input format or password too short/too big:

    * 4a1. The system catches the invalid input during validation.

    * 4a2. The system gracefully rejects the registration request, ensuring no internal implementation details are exposed.

    * 4a3. The system informs the user of the password and email requirements and prompts them to try again.

5. a) Email already exists:

    * 5a1. The system determines the requested email is already registered in the database.

    * 5a2. The system gracefully informs the user that the email is taken.

    * 5a3. The system prompts the user to choose a different email.



# UC7: User Authentication

**Primary Actor:** User or Admin

**Scope/Goal:** The authentication layer of the Climate-Driven Energy Demand Analytics System. The goal is to mediate and restrict access to the system's protected functionalities based on user roles. The system must verify credentials and grant standard users access to model execution and prediction generation, while granting admins full access, including model training functionality.

**Level:** User Goal

**Stakeholders and Interests:**

* **Standard User:** Needs to seamlessly authenticate to execute models, generate predictions, and access evaluation results.
* **Admin:** Needs to seamlessly authenticate to access all system features, including triggering model training.
* **Security Administrator:** Needs assurance that all authentication attempts are reliably logged.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user must have previously registered an account with a username, an email and a password.


**Main Success Scenario:**

1. The user opens/accesses the application.

2. The system prompts the user for their email and password credentials.

3. The user inputs their previously registered credentials.

4. The system performs input validation to prevent trivial misuse.

5. The system queries the database to validate the user, hashing the provided password and comparing it against the stored cryptographic hash.

6. The system logs the successful authentication attempt, recording the timestamp and the user's email and username.

7. The system grants the user access to the app's protected functionalities based on their role.

**Extensions:**

3. a) The user does not have an account:

    * 3a1. The user opts to register rather than log in.

    * 3a2. The system redirects the user to the User Registration flow (UC6 - User Registration).

4. a) Trivial misuse or invalid input format detected:

    * 4a1. The system catches the invalid input during validation.

    * 4a2. The system logs the failed authentication attempt due to invalid input, recording the timestamp and the attempted email.

    * 4a3. The system denies access and prompts the user again for their credentials.

5. a) Invalid login attempt (incorrect password or unrecognized email):

    * 5a1. The system determines the validation check failed in the database.

    * 5a2. The system gracefully rejects the request, ensuring no stack traces or internal implementation details are exposed to the user.

    * 5a3. The system logs the failed authentication attempt, recording the timestamp, the attempted email, and the username (considering the email was found in the database).
    
    * 5a4. The system denies access and prompts the user again for their credentials.



# UC8: Analytics Dashboard

**Primary Actor**:
Developer

**Scope/Goal**: The goal is to present a dashboard to an admin user, consolidating results from multiple background processes (e.g: prediction) into a single location to facilitate data queries and the visualization of key interests.

**Level**:
User Goal

**Stakeholders and Interests**:

* **Data cientist/engineer**: Wants to quickly consult information through a simple and intuitive interface, without running manual scripts.

* **Security administrator**: Needs to ensure that only users who passed the authentication (UC7) can view the data.

* **Developer**: Wants to ensure that the complex logic of the backend is presented clearly and correctly to the end-user.

**Preconditions**:
1. The user has successfully logged into the system.

2. The entire data pipeline, from automated ingestion and cleaning to the predictive model execution, is fully functional.

**Main Success Scenario**:
1. The use case starts when the authorized user accesses the Dashboard section.

2. The system presents a unified view containing information about the data and system status, such as:

    - Climate-Energy correlations and relevant features: Visualizations of how weather variables impacted past demand.

    - Forecast summaries: Expected energy peaks and trends for the upcoming period.

    - Pipeline status: Information on the last successful data ingestion and model training.

    - Last query/request history: a dedicated visualization/section showing the parameters (date range,variables) of the most recent query performed by the user.

3. The system provides filtering and query tools, allowing the user to isolate specific dates or climate conditions.

4. The user reviews the integrated information to gain insights into the energy-climate relationship.

5. The system logs the execution time for the operation chosen by the user.

**Extensions:**

2.  a) No previous query history found:

    * 2a1. The system displays a "no history found" message. 

    * 2a2. The system suggests a default visualization (e.g., the last 24 hours).

    b) No data available to display:
    
    * 2b1. The system informs the user that the pipeline needs to be executed before results can be shown.

    * 2b2. The system may provide a button to trigger the data update process considering the user has the required permissions.

3.  a) Incompatibility with current data:

    * 3a1. The last query used a date range that isn´t available in the memory or cache: the system notifies the user and suggests the nearest available period.