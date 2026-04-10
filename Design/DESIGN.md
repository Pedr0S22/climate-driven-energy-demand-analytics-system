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

* **Target APIs Data Extractiion:** ENTSO-E Transparency Platform (Energy Demand) & Copernicus Climate Data Store ERA5-Land (Meteorological Data).
* **Orchestration:** Driven by a master `data_retrieval(start_date, end_date, country_code)` function that sequentially triggers energy data fetching, weather data fetching, and finally, cloud backup.
### 2.1.1. Core Logic & Mechanisms:

  - **Input Validation & Idempotency:** The module strictly validates that `start_date` is not strictly after `end_date`. It features an idempotency check: before querying external APIs, the script checks if the target CSV already exists in the local directories (`/data/raw/weather/` and `/data/raw/energy/`). If it does, the expensive API call is skipped to save time and quota.

  - **Resilience & Exponential Backoff:** Both fetching mechanisms are wrapped in a robust retry loop (configured globally via `MAX_RETRIES = 3`). If an API connection fails, times out, or returns a corrupted file, the script applies an exponential backoff (`2^attempt` seconds) before retrying, preventing rapid-fire failures and handling temporary network drops gracefully.

  - **ENTSO-E (Energy Data):**
    - Utilizes the `EntsoePandasClient` authenticated via an API key loaded from a `.env` file.
    - Automatically localizes timestamps to the `Europe/Madrid` timezone.
    - Applies a mathematically precise `+ 1 day` timedelta to the user-supplied `end_date` to ensure the API captures the absolute final hours of the requested boundary.
    - Renames the output column to `Load_MW` and saves the raw output as a CSV specifically tagged with the target country code (for now, `ES` for Spain).

  - **Copernicus ERA5-Land (Weather Data):**
    - Uses the `cdsapi.Client()` to fetch 11 specific meteorological variables (e.g., 2m temperature, skin temperature, 10m wind components, solar radiation) for a fixed geographical bounding box (longitude: -3.7, latitude: 40.4).
    - The CDS API natively returns data packaged in a `.zip` archive. The script safely downloads this to a temporary local path (`temp_zip_path`), unpacks it into memory, renames the inner contents to match the project's standardized naming convention, and automatically purges the `.zip` residue.
    - **Edge Case Handling:** Explicitly catches `zipfile.BadZipFile` exceptions. The Copernicus API is known to return plain-text HTML/JSON error messages (like queue timeouts or quota limits) masked as an HTTP 200 ZIP download. The script safely traps this, reads the error snippet for the log, and falls back to the retry mechanism.
  - **Data Backup (`gdrive_sync.py`):**
    - Once local CSVs are securely written, the module triggers `backup_project_data()`.
    - Authenticates with Google Drive via OAuth 2.0 (`credentials.json` and `token.json`).
    - Scans both local raw directories and queries the target Google Drive folders (`WEATHER_DRIVE_FOLDER_ID` and `ENERGY_DRIVE_FOLDER_ID`).
    - Prevents redundant uploads by verifying if the exact file name already exists in the destination Drive folder before initiating the chunked, resumable media upload.


### 2.2. Cleaning & Temporal Alignment Module
* **Target:** Reads from `/data/raw/`, outputs to `/data/processed/`.
* **Logic:** [`TODO`: Define exact Pandas functions used. e.g., df.interpolate() for missing values, timezone localization logic].


### 2.3. Feature Engineering Module
* **Target:** Reads from `/data/processed/`, outputs to `/data/feat-engineering/`.
* **Logic:** [`TODO`: Define the exact formulas/functions for the rolling window features and lagged features].


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

### 3.2.1 API Contrancts for Prediction Service [`TODO`]

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
