# USE CASE DEFINITIONS - V3.3

This file contains all UCs for the development of this project.

# DATA PIPELINE UCS

## UC1: Data Ingestion

**Primary Actor:** Data Scientist / Developer

**Scope/Goal:** The data ingestion layer of the Climate-Driven Energy Demand Analytics System.The goal is to retrieve electricity demand data from "ENTSO-E" dataset found at [https://transparency.entsoe.eu/]  and climate data from "ERA5
Land Hourly data from 1950 to present" dataset found at [https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=overview]. The ingestion process must be reproducible and executable through code.

**Level:** User Goal

**Stakeholders and Interests:**

* **Client:** Needs the system to securely ingest real-world data from stable, publicly available international datasets to explore how climate affects electricity demand.
* **Developer / Data Scientist:** Needs to execute the data ingestion script reliably, ensure raw data is stored in a dedicated raw-data directory without manual modification.
* **Security Administrator:** Needs absolute certainty that no credentials or API keys are hardcoded in the repository and that configuration files such as `.env` are excluded from version control.

**Preconditions:**

1. API credentials for ENTSO-E and Copernicus are securely configured using environment variables.
2. The system must be configured to target one selected European country and a timeframe of 6 years of data (from 2020 to 2025).


**Main Success Scenario:**

1. The Developer / Data Scientist executes the data ingestion script via the command line, allowing it to run until all data for the specified 6-year range is retrieved.
2. The system begins measuring the execution time for the data ingestion component.
3. The system connects to the ENTSO-E Transparency Platform and retrieves the primary target variable which is total electricity load, expressed in megawatts (MW)
4. The system connects to the Copernicus Climate Data Store (ERA5 dataset) and retrieves meteorological data. Specifically, it extracts:

    * Skin temperature (in Kelvin)
    * 2-meter air temperature (in Kelvin)
    * 2-meter dewpoint temperature (in Kelvin)
    * soil temperature level 1 (in kelvin)
    * Surface solar radiation downwards (in J/m²)
    * Surface thermal radiation downwards (in J/m²)
    * Surface pressure (in Pa)
    * 10-meter wind speed (both Eastward and Northward) (in m/s)
    * Volumetric soil water layer 1 (in m³/ m³)
    * Total precipitation (in m)

    **For further familiarization and better explanation regarding the variables mentioend below proceed to the Copernicus Climate Data Store**

5. The system stores the unmodified raw climate data into the `Code\energy_prediction_system\data\raw\weather\` directory.
6. The system stores the unmodified raw electricity data into the `Code\energy_prediction_system\data\raw\energy\` directory.
7. The system automatically backs up and exports all retrieved raw data directories to a private Google Drive.
8. The system successfully logs all events and the execution time into ELK.

**Extensions:**

3. a) API connection failure or authentication error with ENTSO-E:

    * 3a1. The system detects that the ENTSO-E Transparency Platform is unreachable or authentication fails.

    * 3a2. The system properly logs the ingestion failure to ELK.

    * 3a3. The system results in a clean termination of the ingestion script.

3) b) Missing or incomplete data returned from ENTSO-E:

    * 3b1. The ENTSO-E API returns gaps, timeouts, or missing records for the requested period.

    * 3b2. The system handles the failure gracefully.

    * 3b3. The system ensures the missing data does not cause an uncontrolled crash.

    * 3b4. The system logs the anomaly to ELK and terminates cleanly .

4. a) API connection failure or authentication error with Copernicus:

    * 4a1. The system detects that the Copernicus Climate Data Store is unreachable or authentication fails.

    * 4a2. The system properly logs the ingestion failure to ELK.

    * 4a3. The system results in a clean termination of the ingestion script.

4) b) Missing or incomplete data returned from Copernicus:

    * 4b1. The Copernicus API returns gaps or missing meteorological records.

    * 4b2. The system handles the failure gracefully.

    * 4b3. The system ensures the missing data does not cause an uncontrolled crash.

    * 4b4. The system logs the anomaly to ELK and terminates cleanly.

## UC2: Data Cleaning and Alignment

**Primary Actor:** Developer

**Scope/goal:** The objective is to clean, validate, align, and standardize the datasets to a common temporal resolution, ensuring data integrity, robustness, and quality before the training phase. The processed data must be stored in `/data/processed/`.

**Level:** User goals

**Stakeholders/Interests:**
- User: Wants to ensure the system uses clean and consistent data to generate reliable forecasts.
- Developer/ Data Analyst: Require reliable and consistent data to ensure robustness in the models and subsequent steps.
- Administrator: Needs assurance that raw data remains untouched and that processed data is stored separately under `/data/processed/`.

**Preconditions:**
- Data ingested must be located in the correct folders: `/data/raw/..`;
- The `/data/processed/` folder must exist;


**Main Success Scenario:**
1. The use case begins when the data preprocessing module is executed.
2. The system loads raw data from `/data/raw/weather/` and `/data/raw/energy/`.
3. The system converts timestamps to the UTC standard and checks for any timezone inconsistencies.
4. The system handles missing values in the all variables ingested.
5. The system handles data types and features conversions.
6. The system detects outliers using the IQR method for all variables except electricity load. For each detected value, the system verifies whether it is plausible according to the predefined limits.
7. The system aggregates data every hour, averaging temperature, wind, radiation, and precipitation; for electrical charge, we use the maximum value for that interval.
8. The system merges both datasets into a single dataset
9. The system aggregates daily dataset using the sum of load_MW for 24h and uses a simple aveage for continous variables.
10. The system saves the processed datasets (daily and hourly) in the `/data/processed/` folder.
11. The system logs all events and the execution time to ELK.


**Extensions:**

3. a) The system detects that not all expected timestamps (15-minute intervals) exist:
    * 3a1.There is a missing time value; what we do is, since the data is for 15 minutes, we add a line for the timestamp that was supposed to be there, and the remaining variables are marked as missing values ​​for later processing.

4. a) Missing Values Detected
    * 4a1. There is 1 isolated missing value per hour:
        - The system applies linear interpolation between the previous and the next value.
    * 4b1. There is more than 1 missing value within a 1-hour interval:
        - The system estimates missing values using statistical methods based on nearby valid observations.
        - For solar radiation, the system considers whether the timestamp corresponds to daytime or nighttime when estimating the value.
        - For precipitation, the system evaluates surrounding observations to determine whether the value should remain zero or be estimated from nearby valid data.

6) a) Outlier detected by IQR
    * 6a1. The value is outside the limits:
        - The system replaces the value using statistical estimates based on nearby valid observations, taking into account the characteristics of each variable;
    * 6a2. The value is outside the IQR but within plausible limits:
        - The system retains the value, considering it a possible outlier.
    
7. a) The timestamps are not all the same time:
    * 7a1. There exists timestamps that do not exactly match xx:00, xx:15, xx:30, or xx:45:
        - The system adjusts them to the nearest 15-minute interval before time aggregation.
    
## UC3: Feature Engineering

**Primary actor**:
Data Scientist/Developer

**Scope/Goal**:
Transform the clean and synchronized data into relevant predictive features (temporal, lagging, rolling, and advanced) to feed the modeling component, from which temporal features, such as: hour, day, month, etc; season rolling climate features, lagged demand features and new derived features.

**Level**:
User goal.

**Stakeholders and Interests**:

* **Data Scientist**: Expects to obtain relevant features that capture trends, seasonality, and complex climate-energy relationships to improve model performance.

* **Data Engineer**: Expects an efficient, modular transformation process that is well-integrated into the system's pipeline.

* **Validator**: Aims to ensure that errors such as data leakage do not occur and that temporal integrity is maintained.

**Preconditions**:
1. The Data Cleaning and Alignment stage has been successfully completed.

2. Synchronized and cleaned data is available in the `/data/processed/ `directory.

3. The system has validated that all required columns and timestamps are present and reliable.

**Main Success Scenario**:
1. The use case starts when the feature engineering module is activated, which occurs once the data cleaning stage is completed;

2. The system loads the data available in the `/data/processed/` directory;

3. The system extracts temporal features, including hour of the day, day of the week, etc, and seasonal indicators.

4. The developer defines the window size and the overlap, constrained by the dataset timestamps, to ensure the rolling windows are physically meaningful;

5. The system extracts rolling climate features, such as:
    - mean;
    - median;
    - standard deviation;
    - variance;
    - root mean square;
    - average derivatives;
    - skewness, kurtosis, and IQR;

6. The system extracts lagged demand features, such as:
    - Hourly dataset:
        - L1 Load: Electrical load one hour ago;
        - L24 Load: Load one day ago;
        - L168 Load: Load one week ago;
    - Daily dataset:
        - L1 Load: Electrical load one day ago;
        - L7 Load: Load one week ago;
        - L28 Load: Load one month ago;

7. The system derives new features from the data to provide additional analytical depth, such as:
    - Temperature Anomalies: Deviation from seasonal/monthly means;
    - Climatic Indicators: Heating Degree Days (HDD) or Cooling Degree Days (CDD);
    - Heatwave/Coldwave Flags: Binary indicators based on persistent extreme temperatures.

8. The system validates that the features obtained don't include invalid values generated during the feature extraction process.

9. The system measures and logs the execution time, relevant feature count, and other processing events.

10. The system saves the full sets in `/data/processed/feat-engineering/`, for both hourly and daily data models, ensuring the output format is compatible with the model training pipeline.

**Extensions**:

8. a) Minor domain inconsistencies detected (e.g., a few records with values that do not align with physical constraints):
    * 8a1. The system handles them by dropping or imputing the affected rows to maintain dataset quality.

    b) Domain inconsistencies detected:
    * 8b1. The system utilizes forward and backward filling to handle invalid values generated during extraction, ensuring a complete dataset for the modeling stage.

    c) High dimensionality detected:

    * 8c1. The system performs feature selection using correlation metrics (labda, spearman, logist regression/ANOVA) to identify the most predictive variables.

    * 8c2. The system performs dimensionality reduction PCA to compress information.

    * 8c3. The system generates and labels these new dataset versions.

    * 8c4. The system saves each resulting dataset version as a separate file to allow for comparative training and evaluation in the next stage (full, selected, pca feature sets) for both daily and hourly models.

    * 8c5. The system ensures these new versions are compatible with the model training pipeline.



## UC4: Modeling & Evaluation

**Primary Actor:** Data Scientist

**Scope/Goal:** Use the optimized and reduced datasets from the Feature Engineering module to train regression models, evaluate their statistical performance, and select the best version for production through a temporal splitting strategy.

**Level:** User Goal

**Stakeholders and Interests**
* **Administrator:** Requires a protected interface to trigger training and compare different data variants.
* **Project Supervisor:** Demands the application of rigorous metrics ($R^{2}$, MAE, RMSE) and the absolute prohibition of shuffling in time-series data.

**Preconditions**
1.  **Feature Engineering Success:** Datasets with different reduction techniques are available in the `/data/processed/` directory, including data with and without feature engineering (`/data/processed/feat-engineering`).
2.  **Data History:** Availability of a 6-year data history processed.

**Main Success Scenario**
1.  The system loads the processed and feature-engineered electricity load and climate data from the `/data/processed/` directory.
2.  The system applies a 3 different temporal splits (Expanding Window Walk-Forward; The Fixed Rolling Window; Nested Time-Series Split (Walk-Forward + Final Holdout)) to maintain the chronological order of the data;
3.  For both **Daily** and **Hourly** resolutions, the system executes the training for:
    * **Linear Regression**
    * **Random Forest**
4.  The system calculates mandatory performance metrics ($MAE$, $RMSE$, and $R^{2}$) for each model at each resolution.

    **Note:** Additional metrics may be computed as needed for further diagnostic purposes.

5.  The system performs **residual analysis** to identify potential overfitting.
6.  The system automatically selects the best-performing model for each tested algorithm (e.g., the best Random Forest and the best Linear Regression) for both daily and hourly resolutions based on the validation metrics.
7.  The system detects the top-2 drivers for the regression predictions.
8.  The system persists the winning models, the evaluation metrics and top-2 feature drivers and logs the training event, including the username and a timestamp to ELK.


**Extensions**
* **1a. Inconsistency in data within `/data/processed/`:**
    * 1a1. The system detects a failure in the presence of mandatory columns.
    * 1a2. The system terminates the process gracefully, reporting the error in the log.

* **6a. Failure in statistical tests (e.g., insufficient variance):**
    * 6a1. The system uses the $R^{2}$ metric as a tie-breaker and notifies the Administrator in the report.


# APPLICATION UCS


## UC5: User Registration

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

8. The system logs the successful account creation, recording the timestamp and the new user's email and username to ELK.

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



## UC6: User Authentication

**Primary Actor:** User or Admin

**Scope/Goal:** The authentication layer of the Climate-Driven Energy Demand Analytics System. The goal is to mediate and restrict access to the system's protected functionalities based on user roles. The system must verify credentials and grant standard users access to model execution and prediction generation, while granting admins full access, including model training functionality.

**Level:** User Goal

**Stakeholders and Interests:**

* **Standard User:** Needs to seamlessly authenticate to execute models, generate predictions, and access evaluation results.
* **Admin:** Needs to seamlessly authenticate to access all system features, including triggering model training.
* **Security Admin:** Needs assurance that all authentication attempts are reliably logged.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user must have previously registered an account with a username, an email and a password.


**Main Success Scenario:**

1. The user opens/accesses the application.

2. The system prompts the user for their email and password credentials.

3. The user inputs their previously registered credentials.

4. The system performs input validation to prevent trivial misuse.

5. The system queries the database to validate the user, hashing the provided password and comparing it against the stored cryptographic hash.

6. The system logs the successful authentication attempt, recording the timestamp and the user's email and username to ELK.

7. The system grants the user access to the app's protected functionalities based on their role.

**Extensions:**

3. a) The user does not have an account:

    * 3a1. The user opts to register rather than log in.

    * 3a2. The system redirects the user to the User Registration flow (UC6 - User Registration).

4. a) Trivial misuse or invalid input format detected:

    * 4a1. The system catches the invalid input during validation.

    * 4a2. The system logs the failed authentication attempt due to invalid input, recording the timestamp and the attempted email to ELK.

    * 4a3. The system denies access and prompts the user again for their credentials.

5. a) Invalid login attempt (incorrect password or unrecognized email):

    * 5a1. The system determines the validation check failed in the database.

    * 5a2. The system gracefully rejects the request, ensuring no stack traces or internal implementation details are exposed to the user.

    * 5a3. The system logs the failed authentication attempt, recording the timestamp, the attempted email, and the username (considering the email was found in the database) to ELK.
    
    * 5a4. The system denies access and prompts the user again for their credentials.



## UC7: Daily Prediction Generation

**Primary Actor:** User

**Scope/Goal:** Allow the user to obtain electricity demand predictions (in MW) for a specific period in days using trained models.

**Level:** User Goal

**Stakeholders and Interests**
* **User:** Seeks fast, accurate predictions to plan consumption or analyze trends.
* **System Admin:** Ensures only registered and authenticated users access prediction functionality.

**Preconditions**
1.  **Authentication:** The user must be successfully authenticated in the system.
2.  **Model Availability:** A daily prediction model must be trained, persisted and accessible for prediction.
3.  **Data Infrastructure:** The `/data/processed/` directory must contain the necessary climate and energy features to support lag and rolling calculations.


**Main Success Scenario**

1.  The user requests a daily prediction using the system's default parameters (3 historical days and 7 forecast days).
2. The system retrieves the corresponding historical energy and climate data from the processed data directory.
3.  The system utilizes the active daily model to calculate the demand prediction and dynamically identifies the top 2 variables (drivers) most heavily influencing this specific forecast.
4.  The system logs the action, including the username, timestamp, and input parameters to ELK.
5.  The system delivers the calculated prediction result to the user, including the forecast values and the top 2 drivers, via the dashboard described in UC10.

**Extensions**

1. a. User requests a custom prediction timeframe:

    * 1a1. The user selects a custom number of historical days (between 1 to 5) and/or forecast days (between 1 to 14).

    * 1a2. The system proceeds to Step 2 using the newly specified parameters.

3) a. Prediction model fails to execute for the first time after opening the application with default parameters values:

    * 3a1. The system catches the execution error.

    * 3a2. The system logs the failure details to ELK.

    * 3a3. The system displays a generic error message to the user stating the prediction service is currently unavailable.

3. b. Prediction model fails to execute after the user requests a new prediction with custom parameter values:

    * 3b1. The system catches the execution error.

    * 3b2. The system logs the failure details to ELK.

    * 3b3. The system displays the error in a pop-up described in UC10 (extension 8).





## UC8: Hourly Prediction Generation

**Primary Actor:** User

**Scope/Goal:** Allow the user to obtain electricity demand predictions (in MW) for a specific period in hours using trained models.

**Level:** User Goal

**Stakeholders and Interests**
* **User:** Seeks fast, accurate predictions to plan consumption or analyze trends.
* **System Administrator:** Ensures only registered and authenticated users access prediction functionality.

**Preconditions**
1.  **Authentication:** The user must be successfully authenticated in the system.
2.  **Model Availability:** An hourly prediction model must be trained, persisted and accessible for prediction.
3.  **Data Infrastructure:** The `/data/processed/` directory must contain the necessary climate and energy features to support lag and rolling calculations.


**Main Success Scenario**

1.  The user requests an hourly prediction using the system's default parameters (3 historical hours and 12 forecast hours).
2. The system retrieves the corresponding historical energy and climate data from the processed data directory.
3.  The system utilizes the active hourly model to calculate the demand prediction and dynamically identifies the top 2 variables (drivers) most heavily influencing this specific forecast.
4.  The system logs the action, including the username, timestamp, and input parameters to ELK.
5.  The system delivers the calculated prediction result to the user, including the forecast values and the top 2 drivers, via the dashboard described in UC11.

**Extensions**

1. a. User requests a custom prediction timeframe:

    * 1a1. The user selects a custom number of historical hours (between 3 to 5) and/or forecast hours (between 1 to 24).

    * 1a2. The system proceeds to Step 2 using the newly specified parameters.

3) a. Prediction model fails to execute for the first time after opening the application with default parameters values:

    * 3a1. The system catches the execution error.

    * 3a2. The system logs the failure details to ELK.

    * 3a3. The system displays a generic error message to the user stating the prediction service is currently unavailable.

3. b. Prediction model fails to execute after the user requests a new prediction with custom parameter values:

    * 3b1. The system catches the execution error.

    * 3b2. The system logs the failure details to ELK.

    * 3b3. The system displays the error in a pop-up described in UC11 (extension 8).




## UC9: Administrative Model Management

**Primary Actor:** Administrator (admin)

**Scope/Goal:** To allow the Administrator to view all available machine learning models in the database, evaluate their performance metrics, and select which specific models will be active and utilized by the system for generating daily and hourly predictions.

**Level:** User Goal

**Stakeholders and Interests:**

* **Administrator:** Wants a reliable and data-driven options to compare model accuracy and assign active models without requiring code changes or deployments.

* **Data Scientists:** Want the models they train, evaluate, and push to the database to be visible and selectable for production use.

* **Regular User:** Relies on the system to seamlessly use the most accurate, Admin-approved models when they request their predictions.

**Preconditions:**

1. The user has successfully authenticated into the application and has an "Admin" role.

2. The user has navigated to the "Model Management" section.

3. Evaluated prediction models, along with their baseline training metrics (e.g., MAE, RMSE, R-squared), are stored and available in the database.

**Main Success Scenario:**

1. The Administrator requests access to the Model Management.

2. The system fetches and displays a list of all available daily and hourly prediction models (the winning algorithms saved from UC4) from the database.

3. The system presents the models in a comparative view (e.g., a table or by row) for each hourly and daily model-types, displaying their respective performance metrics (MAE, RMSE, R-squared) side-by-side.

4. The system visually indicates which models are currently set as "active" for daily and hourly predictions.

5. The Administrator reviews the metrics to determine the most accurate models.

6. The Administrator selects a newly desired model from the list to be the active model for daily and/or hourly predictions.

7. The Administrator saves/submits the changes.

8. The system updates the global configuration in the database.

9. The system applies the selected models to all future prediction requests across the application.

10. The system displays a success confirmation pop-up message to the Administrator and the visual active models modifications.

11. The System logs every event into ELK.

**Extensions:**

2. a. The system encounters an error connecting to the database while fetching models:

    * 2a1. The system catches the error and aborts the loading process.

    * 2a2. The system displays an error message notifying the Administrator that the model list cannot be loaded.

6) a. The Administrator wants to update only the daily or hourly prediction model:

    * 6a1. The Administrator changes the daily or hourly model, leaves the other model selection unchanged, and proceeds to Step 7.


8. a. The system encounters an error saving the configuration to the database:

    * 8a1. The system aborts the update to ensure no active models are broken (rollback).

    * 8a2. The system displays an error message pop-up notifying the Administrator that the changes were not saved.



## UC10: Daily Prediction Dashboard

**Primary Actor:** User


**Scope/Goal:**
Allow the user to access a dashboard to view the time series of the daily electricity demand prediction, comparing the recent actual data with the upcoming forecast, and identifying the main variables driving the trend.


**Level:** User Goal

**Stakeholders and Interests:**
- User: Wants to check the daily electricity demand forecast and adjust the timeframe for planning or analysis purposes.
- Administrator: Wants to ensure that the dashboard loads efficiently and that prediction requests do not overload the backend.


**Preconditions:**
1. The user must already be authenticated.
2. The daily prediction (3 days actual / 7 days forecast default) is available.


**Main Success Scenario:**
1. The user accesses the daily prediction dashboard page.
2. The system uses the default electricity demand prediction (last 3 days actual, next 7 days forecast).
3. The system renders a time series chart displaying the continuous trend from actual values to predicted values.
4. The system displays visual indicators with the main 2 variables associated with the forecast.
5. The user hovers or interacts with the chart to view the precise demand values for specific individual days.
6. The user adjusts the parameters for the chart, changing the historical context (between 1 to 5 days) and the forecast horizon (between 1 to 14 days).
7. The user asks for a new prediction based on the new parameters.
8. The system retrieves the recalculated prediction and smoothly updates the chart and top 2 drivers.
9. The System logs every event into ELK.


**Extensions:**

8) a. The system fails to retrieve the recalculated prediction (e.g., network error or backend failure):

    * 8a1. The system displays a brief error message pop-up notifying the user that the custom timeframe prediction could not be loaded.

    * 8a2. The system retains the currently displayed chart data without breaking the UI.



## UC11: Hourly Prediction Dashboard

**Primary Actor:** User


**Scope/Goal:**
Allow the user to access a dashboard to view the time series of the hourly electricity demand prediction, comparing the recent actual data with the upcoming forecast, and identifying the main variables driving the trend.


**Level:** User Goal

**Stakeholders and Interests:**
- User: Wants to check the hourly electricity demand forecast and adjust the timeframe for planning or analysis purposes.
- Administrator: Wants to ensure that the dashboard loads efficiently and that prediction requests do not overload the backend.


**Preconditions:**
1. The user must already be authenticated.
2. The hourly prediction (3 hours actual / 12 hours forecast default) is available.


**Main Success Scenario:**
1. The user accesses the hourly prediction dashboard page.
2. The system uses the default electricity demand prediction (last 3 hours actual, next 12 hours forecast).
3. The system renders a time series chart displaying the continuous trend from actual values to predicted values.
4. The system displays visual indicators with the main 2 variables associated with the forecast.
5. The user hovers or interacts with the chart to view the precise demand values for specific individual hours.
6. The user adjusts the parameters for the chart, changing the historical context (between 3 to 5 hours) and the forecast horizon (between 1 to 24 hours).
7. The user asks for a new prediction based on the new parameters.
8. The system retrieves the recalculated prediction and smoothly updates the chart and top 2 drivers.
9. The System logs every event into ELK.


**Extensions:**

8) a. The system fails to retrieve the recalculated prediction (e.g., network error or backend failure):

    * 8a1. The system displays a brief error message pop-up notifying the user that the custom timeframe prediction could not be loaded.

    * 8a2. The system retains the currently displayed chart data without breaking the UI.



## UC12: App Logging

**Primary Actor:** Administrator

**Scope/Goal**: To allow the Administrator to securely monitor, search, and analyze system and application logs through a centralized dashboard powered by the ELK (Elasticsearch, Logstash, Kibana) stack, enabling troubleshooting, auditing, and system health checks.

**Level:** User Goal

**Stakeholders and Interests:**

* **Administrator / DevOps:** Wants a powerful, searchable interface to debug errors, track user activity, and monitor system performance without needing direct server access.

* **Security/System:** Requires reliable capture, indexing, and visualization of application events to maintain a secure and trackable audit trail.

**Preconditions:**

1. The user has successfully authenticated into the application and has an "Admin" role.

2. The ELK stack infrastructure is active, properly configured, and successfully ingesting logs from the application and backend data pipelines.

**Main Success Scenario:**

1. The Administrator requests access to the App Logging interface.

2. The system verifies the user's admin privileges.

3. The system generates a secure, authenticated session or token for the ELK environment.

4. The system redirects the Administrator to the Kibana dashboard.

5. The Administrator interacts directly with the Kibana interface to input search queries, time ranges, and filters.

6. Kibana retrieves and displays the matching log entries and visualizations.

**Extensions:**

4. a) The ELK stack service is unreachable during redirection:

    - 4a1. The system detects a timeout or connection refusal when attempting to route to Kibana.

    - 4a2. The system aborts the redirection.

    - 4a3. The system displays an error message within the app notifying the Administrator that the logging service is temporarily offline.

**Note:** Kibana natively displays its own "No results found" state.


## UC13: Scenario Simulation

**Primary Actor:** User

**Scope/Goal:** Allow the user to run "What-if" simulations by manually defining meteorological and temporal conditions. This allows for testing the model's behavior and understanding how specific variables affect electricity demand without consequences or reliance on real-time data.

**Level:** User Goal

**Stakeholders and Interests:**
*   **User:** Wants to explore how different weather scenarios impact the energy grid (e.g., "How much extra load would a 40ºC day in May create?").
*   **Data Scientist:** Wants to validate model sensitivity and ensure the algorithm responds logically to extreme inputs.

**Preconditions:**
1.  **Authentication:** The user must be successfully authenticated.
2.  **Model Availability:** Both active Daily and Hourly prediction models must be trained, persisted, and available in the system.

**Main Success Scenario:**
1.  The user accesses the **Scenario Simulator** section of the application.
2.  The user selects the Daily Model Resolution.
3.  The system offers a list of **Base Scenario Templates** (e.g., "Typical Spring Day", "Heatwave", "Winter Storm") to pre-fill the parameters. The user must select one of this templates.
4.  The user defines the **Temporal Context**:
    *   **Month:** User selects a month (1-12); the system automatically derives the corresponding **Season**.
    *   **Day of Week:** User selects the specific day (Monday-Sunday).
    *   **Year:** The system utilizes the user's current year to account for long-term demand trends.
5.  The system displays input controls (with frontend validation limits) for the primary meteorological drivers:
    *   2-meter air temperature (t2m)
    *   Surface pressure (sp)
    *   Total precipitation (tp)
    *   10-meter wind components (u10 and v10)

6.  The user modifies none, one or more of these parameters. Other features required by the model (e.g., lagged load, rolling climate statistics) are automatically calculated using neutral/median values from the training history.
7.  The user hits the **"Run Simulation"** button.
8.  The system performs **Frontend/Backend Validation** to ensure all inputs are within the physical and logical limits defined in the cleaning module (UC2).
9.  The system feeds the synthesized feature vector into the active model.
10. The system calculates the predicted load (MW) and identifies the **Top 2 Drivers** most heavily influencing this result.
11. The system displays the simulation result (Predicted MW) and visual indicators for the drivers on the simulator dashboard.
12. The user can adjust parameters and **Re-run** the experiment to observe changes in real-time.
13. The system logs the simulation event (input parameters, results and timestamps) to ELK for audit and monitoring.

**Extensions:**

2. a. **The user selects the Hourly resolution:**
    *   2a1. The user selects the specific **Hour of the Day** (0-23) in the Temporal Context section.
    *   2a2. The system continues to Step 3 using the Hourly model.

8) a. **Validation Failure (Invalid Inputs):**
    *   8a1. The system detects inputs that are physically impossible or logically inconsistent.
    *   8a2. The system logs the failure details to ELK
    *   8a3. The system denies the simulation, highlights the offending fields, and prompts the user for correction.

9. a. **The system catches an error during the model's inference phase.:**
    *   9a1. The system logs the failure details to ELK.
    *   9a2. The system displays a pop-up error message to the user.


## UC14: User Logout

**Primary Actor:** User or Admin

**Scope/Goal:** Allow an authenticated user to securely terminate their session, invalidating any active authentication tokens and preventing unauthorized access to their account on the device.

**Level:** User Goal

**Stakeholders and Interests:**
    
*   **User:** Wants to ensure their account is secure when they finish using the application or step away from their device.
*   **Security Administrator:** Needs assurance that sessions are properly terminated, tokens are invalidated or discarded, and the action is logged for auditing.

**Preconditions:**

1.  **Authentication:** The user must be currently authenticated and have an active session in the system.

**Main Success Scenario:**

1.  The user requests to log out of the application via the user interface (e.g., clicking a "Logout" button).
2.  The system invalidates the user's active session and securely clears any locally stored authentication tokens (e.g., JWT).
3.  The system logs the logout event, recording the timestamp, the user's email, and username to ELK.
4.  The system redirects the user to the login/authentication screen.

**Extensions:**

2. a. The system fails to communicate with the backend to invalidate the token (if applicable):
    *   2a1. The system catches the network or server error.
    *   2a2. The system forces a local logout by discarding the token on the client side.
    *   2a3. The system proceeds to Step 3, logging the local logout and the backend communication failure to ELK.