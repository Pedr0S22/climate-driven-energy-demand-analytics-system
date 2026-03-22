# System Design: Climate-Driven Energy Demand Analytics System

This document captures the low-level system design decisions, technical stack, database schemas, and API contracts for the project. It serves as the living technical blueprint for the development team.

## 1. Technology Stack

* **Backend Framework:** Python with FastAPI
* **Data Manipulation & ML:** Pandas, NumPy, SciPy, Scikit-Learn, Optuna
* **Database Engine:** `TODO` SQLite or PostgreSQL
* **Authentication/Security:** JWT for sessions, bcrypt for password hashing.
* **Testing Framework:** pytest framework.
* **Frontend/UI:**  Python PyQt6.

---

## 2. Data Pipeline Internals

Details on the specific classes and scripts executing the machine learning pipeline.

### 2.1. Ingestion Module
* **Target:** ENTSO-E API & Copernicus ERA5 API.
* **Logic:** [`TODO`: Define how the Python script handles data retrieving, retries, and saves raw files].

### 2.2. Cleaning Module
* **Target:** Reads from `/data/raw/`, outputs to `/data/processed/`.
* **Logic:** [`TODO`: Define exact Pandas functions used. e.g., df.interpolate() for missing values, timezone localization logic].

### 2.3. Feature Engineering Module
* **Target:** Reads from `/data/processed/`, outputs to `/data/feat-engineering/`.
* **Logic:** [`TODO`: Define the exact formulas/functions for the rolling window features and lagged features].

### 2.4. Training & Evaluation Module
* **Target:** Reads from `/data/feat-engineering/`, saves to ModelDB.
* **Logic:** [`TODO`Uses TimeSeriesSplit (No random shuffling allowed). Evaluates using MAE, RMSE, R2. Saves output as a serialized model file...]

---

## 3. API Contracts

This section defines the RESTful endpoints the Interface Layer uses to communicate with the Backend Services.

### 3.1. Authentication Layer
* **`POST /api/auth/register`**
  * **Payload:** `{"username": "...", "email": "...", "password": "..."}`
  * **Response:** `201 Created` or `400 Bad Request` (Validation failed).
* **`POST /api/auth/login`**
  * **Payload:** `{"email": "...", "password": "..."}`
  * **Response:** `200 OK` with `{"access_token": "...", "role": "..."}` or `401 Unauthorized` (Generic error).

### 3.2. Prediction Interface
* **`GET /api/predict/daily`**
  * **Headers:** `Authorization: Bearer <token>`
  * **Query Params:** `?date=YYYY-MM-DD`
  * **Response:** `200 OK` with `{"date": "...", "predicted_mw": 4500.5, "features_used": {...}}`
* **`GET /api/predict/hourly`**
  * **Headers:** `Authorization: Bearer <token>`
  * **Query Params:** `?datetime=YYYY-MM-DDTHH:00`
  * **Response:** `200 OK` with `{"datetime": "...", "predicted_mw": 4200.1, "features_used": {...}}`

### 3.3. Admin Controls
* **`GET /api/admin/models`**
  * **Headers:** `Authorization: Bearer <token>` (Admin Only)
  * **Response:** List of all trained models and their metrics.
* **`POST /api/admin/models/activate`**
  * **Headers:** `Authorization: Bearer <token>` (Admin Only)
  * **Payload:** `{"model_id": "..."}`
  * **Response:** `200 OK` (Updates global configuration).

---

## 4. Relational Database Schemas

The system relies on three logical databases/tables: `UserDB`, `ModelDB`, and `PredDB`, as defined in the Architecture.

### 4.1. `users` Table
Stores user credentials and roles. Passwords must be hashed, with a minimum length of 8 characters and maximum of 20 characters enforced before insertion.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | Primary Key | Unique identifier. |
| `username` | String | Unique, Not Null | Chosen username. |
| `email` | String | Unique, Not Null | User's email address. |
| `password_hash` | String | Not Null | Bcrypt hashed password. |
| `role` | String / Enum | Default: 'user' | Defines access level ('user' or 'admin'). |
| `created_at` | Timestamp | Auto-generated| Account creation time. |

### 4.2. `models` Table
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

```
### 4.3. `predictions_log` Table (OR ELK)
Logs user actions and historical predictions.

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / Integer | Primary Key | Unique identifier. |
| `user_id` | Foreign Key | Refers to `users.id`| Who requested the prediction. |
| `model_id` | Foreign Key | Refers to `models.id`| Which model was used. |
| `target_datetime` | Timestamp | Not Null | The date/time being predicted. |
| `predicted_mw` | Float | Not Null | The predicted electricity load. |
| `executed_at` | Timestamp | Auto-generated| When the request was made. |
```