# System Design: Climate-Driven Energy Demand Analytics System

This document captures the low-level system design decisions, technical stack, database schemas, and API contracts for the project. It serves as the living technical blueprint for the development team.

## System Desing Index

### 1. Technology Stack
* #### 1.1. Backend & Machine Learning Stack
* #### 1.2. Frontend & Visualization Stack
* #### 1.3. Infrastructure & Telemetry Stack

### 2. Data Pipeline Design
* #### 2.1. Ingestion Module
* #### 2.2. Cleaning & Temporal Alignment Module
* #### 2.3. Feature Engineering Module
* #### 2.4. Training & Evaluation

### 3. Core Backend Services Design
* #### 3.1.Authentication/Registration & Security Services
* #### 3.2. Prediction Inference Service
* #### 3.3. Administrator & Management Services
* #### 3.4. Live Data Scheduler Service

### 4. Databases & Data Storage Design
* #### 4.1. Relational Database - PostgreSQL
* #### 4.2. File Storage System
* #### 4.3. Log Storage ELK

### 5. Frontend UI & Dashboard Design
* #### 5.1. Application State Management
* #### 5.2. View Layouts & Navigation
* #### 5.3. Data Visualization

### 6. Telemetry & Observability Design
* #### 6.1. Application Log Formatting
* #### 6.2. Logstash Parsing Rules


## 1. Technology Stack

The technology stack used in the project is described below. Also FILE X and FILE Y ....

### 1.1. Backend & Machine Learning Stack

* **Backend Framework:** Python with FastAPI
* **Database Engine:** PostgreSQL; [`TODO`] Files for ML models; ELK stack for logging.
* **Authentication/Security:** JWT for sessions, bcrypt for password hashing.
* **Data Manipulation & ML:** Pandas, NumPy, SciPy, Scikit-Learn, Optuna
* **Testing Framework:** pytest.

### 1.2. Frontend & Visualization Stack

* **Frontend/UI:**  Python PyQt6.
* **Dashboards:** D3.js integrated with PyQt6.

### 1.3. Infrastructure & Telemetry Stack

* **Monitoring:** [`TODO`] ELK


## 2. Data Pipeline Design

Details on the specific classes and scripts executing the machine learning pipeline.

### 2.1. Ingestion Module

The primary objective of Ingestion Module is to reliably, securely, and reproducibly acquire external raw data and safely land it into the system's storage without altering its original state.

* **Target APIs Data Extraction:** ENTSO-E Transparency Platform (Energy Demand) & Copernicus Climate Data Store ERA5-Land (Meteorological Data).
* **Orchestration:** Driven by a master `data_retrieval(start_date, end_date, country_code)` function that sequentially triggers energy data fetching, weather data fetching, and finally, cloud backup.

### 2.1.1. Core Logic & Mechanisms:

  - **Input Validation & Idempotency:** The module strictly validates that `start_date` is not strictly after `end_date`. It features an idempotency check: before querying external APIs, the script checks if the target CSV already exists in the local directories (`/data/raw/weather/` and `/data/raw/energy/`).
    - **Engineering Why:** API quotas are restricted and calls are computationally/network expensive; skipping redundant fetches ensures resource efficiency and faster development cycles.

  - **Resilience & Exponential Backoff:** Both fetching mechanisms are wrapped in a robust retry loop (configured globally via `MAX_RETRIES = 3`).
    - **Engineering Why:** External APIs frequently experience transient outages or rate-limiting; exponential backoff (`2^attempt` seconds) allows the remote server to recover while preventing "thundering herd" failures from our system.

  - **ENTSO-E (Energy Data):**
    - Utilizes the `EntsoePandasClient` authenticated via an API key loaded from a `.env` file.
    - Automatically localizes timestamps to the `Europe/Madrid` timezone.
    - Applies a mathematically precise `+ 1 day` timedelta to the user-supplied `end_date`.
    - **Engineering Why:** Due to timezone offsets (UTC vs Europe/Madrid) and potential sampling overlaps at the end of the day, fetching an extra 24 hours ensures that the absolute final hours of the requested boundary are captured without truncation.

  - **Copernicus ERA5-Land (Weather Data):**
    - Uses the `cdsapi.Client()` to fetch 11 specific meteorological variables for a fixed geographical bounding box.
    - Handles temporary ZIP archives, memory-efficient unpacking, and standardized renaming.
    - **Edge Case Handling:** Explicitly catches `zipfile.BadZipFile`.
    - **Engineering Why:** The Copernicus API sometimes returns plain-text HTML error messages (e.g., "Queue full") masked as an HTTP 200 ZIP download. Catching this allows the system to log the actual server error and trigger a retry rather than crashing on a corrupted ZIP parse.

  - **Data Backup (`gdrive_sync.py`):**
    - Once local CSVs are securely written, the module triggers `backup_project_data()`.
    - Authenticates with Google Drive via OAuth 2.0 (`credentials.json` and `token.json`).
    - Scans both local raw directories and queries the target Google Drive folders (`WEATHER_DRIVE_FOLDER_ID` and `ENERGY_DRIVE_FOLDER_ID`).
    - Prevents redundant uploads by verifying if the exact file name already exists in the destination Drive folder before initiating the chunked, resumable media upload.
    - **Engineering Why:** Redundancy is critical for research reproducibility. By syncing to Google Drive, the team maintains a shared, persistent source of truth for raw data that survives local environment resets.


### 2.2. Cleaning & Temporal Alignment Module

The primary objective of the Cleaning & Temporal Alignment Module is to transform raw, heterogeneous energy and meteorological data into a synchronized, clean, and hourly-aggregated dataset ready for feature engineering. It bridges the gap between raw API outputs (often containing gaps, outliers, or mixed frequencies) and the strict requirements of time-series modeling.

*   **Target:** Reads from `/data/raw/energy/` and `/data/raw/weather/`, outputs to `/data/processed/`.
*   **Core Logic & Mechanisms:**

    - **Energy Data Processing:**
        - **Frequency Detection & Alignment:** Automatically identifies 1h, 15-min, or mixed sampling. Standardizes the grid by filling missing timestamps.
        - **Intelligent Imputation:** Missing `Load_MW` values are handled based on the gap size:
            - **Single-point gaps:** Linear interpolation (`df.interpolate(method="linear")`).
            - **Multi-point gaps:** Mean of the 6 preceding valid observations.
            - **Engineering Why:** Linear interpolation handles isolated missing points smoothly. For larger gaps, the mean of the last 6 observations (1.5 hours) provides a "local steady-state" estimate that avoids creating artificial trends (which interpolation would do) or introducing future-leakage (which backfilling would do).
        - **Max-Aggregation:** Collapses 15-minute intervals into hourly grains using the **maximum** load value.
          - **Engineering Why:** In energy demand forecasting, resource planning is driven by **peak load**. Averaging 15-min peaks would smooth out the highest demand signals, leading to an under-estimation of system stress.

    - **Weather Data Normalization:**
        - **Unit Conversion:** Standardizes raw ERA5-Land units (e.g., Kelvin to Celsius, Pa to hPa, J/m² to W/m²).
          - **Engineering Why:** Standardizes features to physically intuitive scales and numerically stable ranges, facilitating faster model convergence and better interpretability.
        - **Outlier Detection (Dual-Pass):** IQR filtering (1.5 * IQR) combined with hard domain-specific boundaries.
          - **Engineering Why:** Statistical IQR is sensitive to extremes. Physical limits (e.g., temperature between -40°C and 55°C) ensure that we don't discard legitimate extreme weather events (like heatwaves) unless they are truly physically impossible.
        - **Variable-Specific Imputation:**
            - *Thermal/Radiation:* Mean of 4 preceding and 2 subsequent values.
            - *Wind/Pressure/Soil:* Rolling mean of 3 to 6 preceding observations.
            - *Solar:* Forced to zero during night hours (22h-04h); daytime gaps use local window means.
              - **Engineering Why:** Solar sensors often report noisy non-zero values at night. Hard-coding zero reflects physical reality and removes noise.
        - **Mean-Aggregation:** 15-minute weather readings are averaged to produce representative hourly values.
          - **Engineering Why:** Unlike energy demand (peak-driven), weather impacts on energy are cumulative/ambient. A mean temperature better represents the sustained thermal load on the grid.

    - **Dataset Synchronization:**
        - **Inner Join logic:** The module performs a strict `inner join` on the standardized `datetime` column (UTC).
          - **Engineering Why:** The machine learning model requires a complete feature vector to make a prediction. Observations where one source is missing are unusable for training and would introduce bias if naively filled.
        - **Output Generation:** Persists the final synchronized dataframe to `/data/processed/` as `dados_treino_completos.csv` or `dados_predicao.csv`.

    - **Cleaned Data Dictionary:**

| Variable | Description | Unit | Aggregation (Hourly) |
| :--- | :--- | :--- | :--- |
| `datetime` | Standardized timestamp (UTC) | ISO 8601 | Join Key |
| `Load_MW` | Actual electricity demand | MW | **Maximum** |
| `t2m` | 2m Air Temperature | °C | Mean |
| `skt` | Skin Temperature | °C | Mean |
| `d2m` | 2m Dewpoint Temperature | °C | Mean |
| `stl1` | Soil Temperature Level 1 | °C | Mean |
| `ssrd` | Surface Solar Radiation Downwards | W/m² | Mean |
| `strd` | Surface Thermal Radiation Downwards | W/m² | Mean |
| `sp` | Surface Pressure | hPa | Mean |
| `tp` | Total Precipitation | mm | Mean |
| `u10` | 10m U-component of Wind | m/s | Mean |
| `v10` | 10m V-component of Wind | m/s | Mean |
| `swvl1` | Volumetric Soil Water Layer 1 | m³/m³ | Mean |


### 2.3. Feature Engineering Module

The primary objective of the Feature Engineering Module is to transform synchronized hourly data into a high-dimensional feature set that captures temporal patterns, climate inertia, and physics-based demand drivers.

*   **Target:** Reads from `/data/processed/dados_treino_completos.csv`, outputs to `/data/processed/feat-engineering/` (Full, Selected, and PCA versions).
*   **Core Logic & Mechanisms:**

    - **Temporal Decomposition:**
        - Extracts `hour`, `day_of_week`, `month`, `year`, and `season` (1:Winter to 4:Autumn).
        - **Engineering Why:** Captures multi-scale seasonality (daily cycles, weekend vs. weekday patterns, and annual trends) essential for non-stationary energy demand.

    - **Rolling Climate Features (24h Window):**
        - Calculates `mean`, `std`, `median`, `var`, `skew`, and `kurt` for all climate variables.
        - Computes **RMS (Root Mean Square)** and **Deriv (Rate of Change)** for key variables (`t2m`, `skt`, `ssrd`, `tp`).
        - Uses **Rolling IQR** for `t2m` as a robust measure of thermal volatility.
        - **Engineering Why:** A 24-hour window represents a full solar/diurnal cycle. RMS captures the "energy" of weather signals, while the derivative identifies rapid cooling or heating events that trigger immediate spikes in HVAC usage.

    - **Lagged Demand Features:**
        - Extracts `L1` (momentum), `L24` (daily seasonality), and `L168` (weekly seasonality) from `Load_MW`.
        - **Engineering Why:** Energy demand is highly auto-regressive. Today's load at 2 PM is historically the best predictor for tomorrow's load at 2 PM.

    - **Physics-Derived Indicators:**
        - **HDD/CDD (Base 18°C):** Heating and Cooling Degree Hours calculated in Celsius.
        - **Thermal Anomalies:** Deviation of current temperature from the monthly mean.
        - **72h Persistent Extremes:** Binary flags for Heatwaves and Coldwaves, triggered only if temperatures stay in the top/bottom 10th percentile for 72 consecutive hours.
        - **Engineering Why:** 18°C is the standard "neutral" temperature where neither heating nor cooling is typically required. The 72h persistence flag captures the "cumulative heat stress" on buildings, where demand remains high even if the temperature dips slightly after a long hot spell.

    - **Handling Early Records (Gaps in Rolling/Lags):**
        - **Hybrid Imputation:** The module uses `.ffill().bfill()` to handle the $N-1$ initial rows where rolling windows or lags are incomplete.
        - **Zero-Filling:** Flags like `heatwave_flag` use `.fillna(0)` to default to a "no-event" state when data is insufficient.
        - **Engineering Why:** Using `bfill()` (back-filling) ensures that the first records of the dataset are not discarded. This maintains the maximum possible training size and keeps the dataset aligned with the original 52k+ row count, which is critical for time-series continuity.

    - **Redundancy & Dimensionality Management:**
        - **Association-Based Filter (0.6 Threshold):** Removes highly collinear variables. Uses **Spearman** for continuous-continuous, **Lambda** for categorical-categorical, and **Logistic Regression Accuracy** for categorical-continuous associations.
        - **Automated PCA Elbow Detection:** Uses the **Knee Point method** (maximum distance to the secant line) to automatically select the optimal number of components for the PCA dataset.
        - **Engineering Why:** Climate data is notoriously collinear (e.g., skin temp vs. air temp). A 0.6 threshold is conservative, ensuring we retain distinct signals while reducing noise. PCA Elbow detection allows the system to compress features without manual tuning as new variables are added.

    - **Persistence:**
        - Saves fitted `StandardScaler`, `PCA`, and `selected_features` list to `/models/feat-engineering/` using `joblib`.
        - **Engineering Why:** Essential for the **Live Data Scheduler**, ensuring that real-time inference data is transformed using the exact same statistical parameters as the training data.


### 2.4. Training & Evaluation Module
* **Target:** Reads from `/data/feat-engineering/`, saves to ModelDB.
* **Logic:** [`TODO`Uses TimeSeriesSplit (No random shuffling allowed). Evaluates using MAE, RMSE, R2. Saves output as a serialized model file...]



## 3. Core Backend Services Design

### 3.1.Authentication/Registration & Security Services
[`TODO`] - (JWT lifecycle, Bcrypt salting details)

#### 3.1.1 API Contrancts for Authentication/Registration [`TODO`]

* **Registration: `POST /api/auth/register`**

  * **Payload:** `{"username": "...", "email": "...", "password": "...", timestamp: "xxx", role: "ROLE_USER"}`
  * **Response:** `201 Created` or `400 Bad Request` (Validation failed).

* **Authentication: `POST /api/auth/login`**
  * **Payload:** `{"email": "...", "password": "...", timestamp: "xxx"}`
  * **Response:** `200 OK` with `{"status": "access_token": "...", "role": "...",}` or `401 Unauthorized` (Generic error).

### 3.2. Prediction Inference Service
[`TODO`] - (How the backend loads model binaries into memory without blocking API threads)

### 3.2.1 API Contracts for Prediction Service [`TODO`]

* **Preditction using daily model: `GET /api/predict/daily`**
  * **Headers:** `Authorization: Bearer <token>`
  * **Query Params:** `?date=YYYY-MM-DD`
  * **Response:** `200 OK` with `{"date": "...", "predicted_mw": 4500.5, "features_used": {...}}`

* **Prediction using hourly model:`GET /api/predict/hourly`**
  * **Headers:** `Authorization: Bearer <token>`
  * **Query Params:** `?datetime=YYYY-MM-DDTHH:00`
  * **Response:** `200 OK` with `{"datetime": "...", "predicted_mw": 4200.1, "features_used": {...}}`


### 3.3. Administrator & Management Services - [`TODO`]


### 3.3.1 API Contrancts for Admin/Management Service [`TODO`]

* **`GET /api/admin/models`**
  * **Headers:** `Authorization: Bearer <token>` (Admin Only)
  * **Response:** List of all trained models and their metrics.
* **`POST /api/admin/models/activate`**
  * **Headers:** `Authorization: Bearer <token>` (Admin Only)
  * **Payload:** `{"model_id": "..."}`
  * **Response:** `200 OK` (Updates global configuration).

### 3.4. Live Data Scheduler Service
[`TODO`] - (Technical implementation: What library runs it? How does it avoid race conditions with the database?)

* **Target:** Runs asynchronously behind the scenes to fetch up-to-date data for the live prediction requests.
* **Logic:** A dedicated background thread or task scheduler periodically triggers a lightweight version of the Ingestion, Cleaning and Feature Engineering pipeline modules. It fetches only the most recent hours/days of data required (that the systems does not have) to satisfy the rolling windows and lag features needed for real-time inference, ensuring the models always have fresh inputs without requiring manual intervention.


## 4. Databases & Data Storage Design

### 4.1. Relational Database - PostgreSQL
[`TODO`] - EDIT

The system relies on three logical databases/tables: `UserDB`, `ModelDB`, and `PredDB`, as defined in the Architecture.

### Table `users`
Stores user credentials and roles. Passwords must be hashed, with a minimum length of 8 characters and maximum of 20 characters enforced before insertion.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | Primary Key | Unique identifier. |
| `username` | String | Unique, Not Null | Chosen username. |
| `email` | String | Unique, Not Null | User's email address. |
| `password_hash` | String | Not Null | Bcrypt hashed password. |
| `role` | String / Enum | Default: 'user' | Defines access level ('user' or 'admin'). |
| `created_at` | Timestamp | Auto-generated| Account creation time. |

### Table `models`
Stores metadata for trained models available in the system.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | Primary Key | Unique identifier. |
| `model_type` | String | Not Null | e.g., 'Linear Regression', 'Random Forest'. |
| `resolution` | String | Not Null | 'Daily' or 'Hourly'. |
| `metrics_json` | JSON/Text | | Stored MAE, RMSE, and R2 scores. |
| `file_path` | String | Not Null | Path to the `.pkl` or `.joblib` file. |
| `is_active` | Boolean | Default: False | Admin flag denoting if this is the active prod model. |
| `created_at` | Timestamp | Auto-generated| When the model was trained. |


### Table `predictions`
Logs user actions and historical predictions.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | Primary Key | Unique identifier. |
| `user_id` | Foreign Key | Refers to `users.id`| Who requested the prediction. |
| `model_id` | Foreign Key | Refers to `models.id`| Which model was used. |
| `target_datetime` | Timestamp | Not Null | The date/time being predicted. |
| `predicted_mw` | Float | Not Null | The predicted electricity load. |
| `executed_at` | Timestamp | Auto-generated| When the request was made. |

[`TODO`]

### 4.2. File Storage System
[`TODO`] - (Directory structures for raw/processed data, and .pkl/joblib model binary storage rules)

### 4.3. Log Storage ELK
[`TODO`] - (What indices you are using for logs if any!!)


## 5. Frontend UI & Dashboard Design

### 5.1. Application State Management
[`TODO`] - (How the app remembers the user's JWT and current active view)

### 5.2. View Layouts & Navigation
[`TODO`] - (Main Dashboard, Admin Panel, Prediction Views)

### 5.3. Data Visualization
[`TODO`] - (D3.js Integration) (How the Python backend passes JSON data to the D3.js components embedded in PyQt6)

### 6. Telemetry & Observability Design

### 6.1. Application Log Formatting
[`TODO`] - (Standardized JSON log payloads for FastAPI)

### 6.2. Logstash Parsing Rules
[`TODO`] - (How ELK ingests the Python logs)
