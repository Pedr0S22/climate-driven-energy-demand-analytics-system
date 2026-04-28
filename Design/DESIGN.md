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

### 7. Deployment & Operations
* #### 7.1. Database Management
* #### 7.2. Docker Environment
* #### 7.3. API Interaction Guide


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



### 3. Core Backend Services Design

The system implements a modular, layered architecture for its backend services, ensuring separation of concerns and maintainability.

### 3.1. Authentication/Registration & Security Services

The security layer provides robust protection for user data and system access, fulfilling strict Quality Attributes (QA10-QA14).

#### 3.1.1. Security Mechanisms
- **JWT Lifecycle:** Authentication tokens are issued as signed JWTs (HS256) with a configurable expiration period.
- **Bcrypt Salting:** All user passwords are hashed using `bcrypt` with unique salts before storage.
- **Role-Based Access Control (RBAC):** Access to endpoints is restricted based on the `sub` (email) and verified against the database roles (`admin`, `client`).
- **Brute Force Protection (QA13):** Accounts are automatically locked for 5 minutes after the 4th consecutive failed login attempt.
- **Generic Failure Messages (QA10):** All authentication failures return generic "Invalid credentials" or "Account locked" messages to prevent username enumeration and leakage of system internals.

#### 3.1.2. Exception Handling Strategy
FastAPI global exception handlers standardize responses:
- **400 Bad Request:** For Pydantic schema validation failures.
- **401 Unauthorized:** For invalid credentials or expired tokens.
- **403 Forbidden:** For account lockouts or insufficient RBAC privileges.
- **404 Not Found:** For non-existent resource requests.
- **500 Internal Server Error:** For unhandled exceptions, ensuring no stack traces are leaked to the client.

#### 3.1.3 API Contracts for Authentication/Registration

* **Registration: `POST /api/v1/auth/register`**
  * **Payload:** `{"username": "...", "email": "...", "password": "..."}`
  * **Response:** `201 Created` with `{"status": 201, "message": "...", "user_id": 123, "timestamp": "..."}`

* **Authentication: `POST /api/v1/auth/login`**
  * **Payload:** `{"email": "...", "password": "..."}`
  * **Response:** `200 OK` with `{"access_token": "...", "token_type": "bearer", "role": "...", "status": 200, "message": "...", "timestamp": "..."}`

* **Logout: `POST /api/v1/auth/logout`**
  * **Headers:** `Authorization: Bearer <token>`
  * **Response:** `200 OK` with `{"status": 200, "message": "Successfully logged out", "user_id": 123, "timestamp": "..."}`


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

The system utilizes PostgreSQL as its primary relational database, structured to ensure data normalization, referential integrity, and efficient queries for predictive time-series data. The schema follows a strict Entity-Relationship model.

#### Base Tables and Role-Based Access Control

The system uses an inheritance pattern to manage different user roles. The central `users` table stores credentials and common data, while `admin` and `client` act as specialized extensions. Passwords are natively managed on the server using the `pgcrypto` extension.

**Table `users`**
Stores base credentials and account security information.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BigSerial | Primary Key | Auto-generated unique identifier. |
| `email` | Text | Unique, Not Null | User email address. |
| `username` | Varchar | Unique, Not Null | Chosen username. |
| `password` | Varchar | Not Null | Password hash. |
| `account_regist_date`| Timestamp | Default: CURRENT_TIMESTAMP | Account creation date and time. |
| `failed_login_att` | Integer | Default: 0 | Counter for failed login attempts. |
| `acc_locked_until` | Timestamp | Nullable | Date and time until the account is locked. |
| `last_failed_att` | Timestamp | Nullable | Date and time of the last failed login attempt. |

**Table `admin` & `client`**
Extensions of the users table that define system privileges.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `users_id` | BigInt | PK, FK | Primary key that also acts as a foreign key with ON DELETE CASCADE. |

#### Models and Requests

The `model` table stores machine learning model metadata, while the `request` table serves as the transaction hub, linking a user to a specific model execution.

**Table `model`**
Stores metadata and performance metrics of the trained models.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `model_name_id` | BIGSERIAL | Primary Key | Unique model identifier. |
| `model_type` | VARCHAR(512) | Not Null | Type of machine learning model. |
| `model_creation_date` | TIMESTAMP | Not Null, Default: CURRENT_TIMESTAMP | Date the model was registered or trained. |
| `model_pred_type` | VARCHAR(512) | Not Null | Type of prediction the model makes (e.g., regression, classification). |
| `model_server_relative_path`| VARCHAR(512) | Not Null | Server path to the model file. |
| `rmse` | DOUBLE PRECISION | Not Null | Root Mean Square Error metric. |
| `mae` | DOUBLE PRECISION | Not Null | Mean Absolute Error metric. |
| `r2` | DOUBLE PRECISION | Not Null | R-squared metric. |

**Table `request`**
Logs the history of prediction requests made by users.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BigSerial | Primary Key | Unique request identifier. |
| `date_req` | Timestamp | Default: CURRENT_TIMESTAMP | Date and time the request was made. |
| `model_model_name_id` | BigInt | FK | Reference to the utilized model. |
| `users_id` | BigInt | FK | User who made the request. |
| `request_type` | VARCHAR(512) | NOT NULL | Specifies the request type (e.g., 'normal' or 'advanced'). |

#### Prediction Results

Predictive results are strictly separated by their temporal granularity into `predictions_daily` and `predictions_hourly`. This prevents null fields in the database and allows highly optimized queries based on the requested time horizon, using composite primary keys to ensure a 1:N relationship with the origin request.

**Table `predictions_daily`**
Stores predictions with daily granularity.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `request_id` | BigInt | PK, FK | The origin request. |
| `date_day` | Date | PK, Not Null | The target day of the prediction. |
| `value_pred` | Double Precision | Not Null | The predicted electricity load value. |

**Table `predictions_hourly`**
Stores predictions with hourly granularity.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `request_id` | BigInt | PK, FK | The origin request. |
| `date_hour` | Timestamp | PK, Not Null | The target hour of the prediction. |
| `value_pred` | Double Precision | Not Null | The predicted electricity load value. |

#### Architectural Rationale and Key Decisions

##### Role-Based Access Control via Table Inheritance
Instead of relying on a single, monolithic `users` table with sparse, nullable columns to accommodate different roles, the database employs a strict "Table-per-Type" inheritance pattern. The `users` table acts as the base entity containing universally required attributes (e.g., authentication credentials, login attempts). Role-specific tables (`admin` and `client`) reference this base table using their primary key as a foreign key. This guarantees zero null-column bloat and makes the system highly extensible if new roles are needed in the future. Furthermore, the aggressive implementation of `ON DELETE CASCADE` across these constraints offloads lifecycle management to the database engine. If a core user account is purged, all associated roles, prediction requests, and generated time-series data are instantaneously and safely destroyed, eliminating the risk of orphaned records.

##### Temporal Segregation of Predictive Data
Machine learning models inherently produce varying resolutions of time-series data. Storing these disparate granularities in a single `predictions` table would necessitate compromised data types (e.g., forcing daily dates into timestamp columns, or leaving columns null) and complex query filtering. By physically segregating `predictions_daily` (using the strict `DATE` type) and `predictions_hourly` (using `TIMESTAMP`), the schema enforces strict data consistency at the column level. The use of composite primary keys (`request_id` coupled with either `date_day` or `date_hour`) elegantly satisfies the 1:N relationship requirement. This allows a single transaction in the `request` table to fan out into hundreds of highly indexed, resolution-specific prediction rows, optimizing the database for fast retrieval by front-end dashboards.

##### Server-Side Cryptography for Database Seeding
Standard practices often expose plaintext passwords during initial database migrations, setup scripts, or CI/CD pipelines. To mitigate this security vulnerability, the architecture leverages PostgreSQL's native `pgcrypto` extension. By shifting the cryptographic workload to the database engine itself, passwords can be hashed and salted dynamically during the `INSERT` operation. This ensures that raw credentials are never stored in SQL dump files, migration logs, or application source code, adhering to strict zero-trust security principles from the moment the database is initialized.
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

## 7. Deployment & Operations

### 7.1. Database Management

The PostgreSQL database is managed via Docker Compose. It is configured to run on port `5433` to avoid conflicts with local PostgreSQL instances.

- **Start Database:**
  ```bash
  docker-compose -f Code/energy_prediction_system/src/databases/docker-compose.db.yml up -d
  ```
- **Stop Database:**
  ```bash
  docker-compose -f Code/energy_prediction_system/src/databases/docker-compose.db.yml down
  ```
- **Initialization:**
  The database automatically initializes using scripts in `Code/energy_prediction_system/src/databases/init-scripts/`:
  - `01-create-tables.sql`: Defines the schema.
  - `02-insert-data.sql`: Seeds the database with initial admin and client users.

### 7.2. Docker Environment

The system uses Docker for containerizing the database and potentially other services (ELK stack, Backend).

- **Prerequisites:** Docker Desktop must be installed and running.
- **Service Isolation:** Currently, the database is isolated in its own compose file to allow for flexible development (running the backend locally or in a container).

### 7.3. API Interaction Guide

Once the backend is running (`python Code/energy_prediction_system/src/api/main.py`), you can interact with the API.

#### Authentication Flow
1. **Register:** `POST /api/v1/auth/register` with username, email, and password.
2. **Login:** `POST /api/v1/auth/login` with email and password. This returns an `access_token`.
3. **Authorized Requests:** Include the token in the header: `Authorization: Bearer <your_token>`.

#### Key Endpoints
- **User Info:** `GET /api/v1/auth/me` (Requires Token)
- **Admin Check:** `GET /api/v1/auth/admin-only` (Requires Admin Role)
- **Predictions (Planned):** `GET /api/predict/daily` and `GET /api/predict/hourly`.

#### Documentation
FastAPI provides interactive Swagger documentation at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
