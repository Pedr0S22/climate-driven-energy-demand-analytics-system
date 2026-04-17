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


### 2.2. Cleaning & Temporal Alignment Module (UC2)

The primary objective of the Cleaning & Temporal Alignment Module is to transform raw, heterogeneous energy and meteorological data into synchronized, clean, and aggregated datasets. Refactored into a modular `DataCleaner` class, it supports both high-performance batch processing of historical files and real-time ingestion for inference.

*   **Target:** Reads from `/data/raw/`, outputs to `/data/processed/` (Batch) or `/data/processed/real-time/` (Real-Time).
*   **Core Logic & Mechanisms:**

    - **Modular Class Design (`DataCleaner`):**
        - Decouples file I/O from transformation logic. It exposes cleaning methods that accept in-memory DataFrames.
        - **Engineering Why:** Enables the **Live Data Scheduler** to process real-time API payloads directly without intermediate disk writes, reducing latency.

    - **Energy Data Processing:**
        - **Time Alignment & Rounding:** Automatically rounds timestamps to the nearest 15-minute mark (xx:00, xx:15, xx:30, xx:45) and fills missing timestamps to ensure a continuous grid.
        - **Rule-Based Imputation:** Missing `Load_MW` values are handled based on frequency:
            - **Isolated (1 NaN per hour):** Linear interpolation.
            - **Multiple (>1 NaN per hour):** Mean of the exactly the **last 6 valid observations**.
        - **Max-Aggregation (Hourly):** Collapses 15-minute intervals into hourly grains using the **maximum** load value.
          - **Engineering Why:** Resource planning is driven by **peak load**.

    - **Daily Aggregation:**
        - Derives a daily dataset from the synchronized hourly data.
        - **Load_MW -> Load_MWh:** Calculated as the **sum** of the 24 hourly load values to represent total daily energy consumption.
        - **Climate Aggregates:** Continuous variables use the **mean** for daily exposure.

    - **Weather Data Normalization:**
        - **Unit Conversion:** Standardizes units (Kelvin to Celsius, Pa to hPa, m to mm, J/m² to W/m²).
        - **Outlier Detection (Dual-Pass):** IQR filtering combined with hard physical domain boundaries (Temperature: -40°C to 55°C, Wind: -69.4 to 69.4 m/s, Precip: 0 to 55 mm).
        - **Variable-Specific Imputation (Vectorized):**
            - *Thermal/Radiation:* Mean of 4 preceding and 2 subsequent valid observations.
            - *Solar:* Forced to zero during night hours (22h-04h).
            - *Wind (u10/v10):* Mean of the last 3 valid observations.
            - *Precipitation:* Forced to zero if surrounded by zeros; otherwise mean of 3 closest valid.

    - **Real-Time Adaptability:**
        - When processing prediction data (`train_data=False`), the system utilizes a dedicated `/real-time/` subfolder and a `prediction_data` prefix. This ensures the production training set remains unpolluted while providing a consolidated history of live inputs.

    - **Cleaned Data Dictionary:**

| Variable | Description | Unit | Aggregation (Hourly) | Aggregation (Daily) |
| :--- | :--- | :--- | :--- | :--- |
| `datetime` | Standardized timestamp (UTC) | ISO 8601 | Join Key | Date Key |
| `Load_MW` / `Load_MWh` | Electricity demand | MW / MWh | **Maximum** | **Sum** |
| `t2m` | 2m Air Temperature | °C | Mean | Mean |
| `skt` | Skin Temperature | °C | Mean | Mean |
| `ssrd` | Surface Solar Radiation Downwards | W/m² | Mean | Mean |
| `tp` | Total Precipitation | mm | Mean | Mean |
| `u10` / `v10` | 10m Wind Components | m/s | Mean | Mean |
| `sp` | Surface Pressure | hPa | Mean | Mean |
| `swvl1` | Volumetric Soil Water Layer 1 | m³/m³ | Mean | Mean |


### 2.3. Feature Engineering Module

The primary objective of the Feature Engineering Module is to transform synchronized data into a high-dimensional feature set that captures temporal patterns, climate inertia, and physics-based demand drivers. The refactored `FeatureEngineer` class dynamically adjusts its logic based on the data frequency (**Hourly** vs **Daily**).

*   **Target:** Reads from `/data/processed/complete_train_data_[hourly|daily].csv`, outputs to `/data/processed/feat-engineering/` as `features_[hourly|daily]_[full|selected|pca].csv`.
*   **Core Logic & Mechanisms:**

    - **Temporal Decomposition:**
        - **Hourly:** Extracts `hour`, `day_of_week`, `month`, `year`, and `season`.
        - **Daily:** Extracts `day_of_week`, `month`, `year`, and `season` (skips `hour` as it is uniform).
        - **Engineering Why:** Captures multi-scale seasonality essential for non-stationary energy demand.

    - **Frequency-Aware Rolling Features:**
        - **Hourly:** Uses a **24-period** window to represent a full solar/diurnal cycle.
        - **Daily:** Uses **7-period** and **30-period** windows to capture weekly inertia and broader monthly trends.
        - **Stats:** Calculates `mean`, `std`, `median`, `var`, `rms`, `deriv`, `skew`, `kurt`, and `iqr`.
        - **Engineering Why:** RMS captures the "energy" of weather signals, while the derivative identifies rapid cooling or heating events.

    - **Lagged Demand Features:**
        - **Hourly:** Extracts `L1` (momentum), `L24` (daily seasonality), and `L168` (weekly seasonality).
        - **Daily:** Extracts `L1` (yesterday), `L7` (weekly cycle), and `L28` (monthly cycle).
        - **Engineering Why:** Energy demand is highly auto-regressive. Daily models rely more on weekly patterns (`L7`) than diurnal ones.

    - **Physics-Derived Indicators:**
        - **HDD/CDD (Base 18°C):** Heating and Cooling Degree Hours/Days.
        - **Persistent Extremes:** Binary flags for Heatwaves and Coldwaves.
            - **Hourly:** Requires 72 consecutive hours of extreme temperature.
            - **Daily:** Requires 3 consecutive days of extreme temperature.
        - **Engineering Why:** Captures the "cumulative stress" on the grid, where demand remains high during prolonged extreme weather.

    - **Redundancy & Dimensionality Management:**
        - **Association-Based Filter (0.6 Threshold):** Removes highly collinear variables using Spearman, Lambda, and LogReg accuracy.
        - **Automated PCA Elbow Detection:** Uses the **Knee Point method** to select optimal components, ensuring transformers are saved per frequency (`scaler_[hourly|daily].joblib`).

    - **Persistence:**
        - Saves fitted states to `/models/feat-engineering/` with frequency-specific suffixes.
        - **Engineering Why:** Essential for the **Live Data Scheduler**, ensuring real-time daily or hourly inference uses the exact statistical parameters of the corresponding training set.


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
