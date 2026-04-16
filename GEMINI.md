# GEMINI.md - Climate-Driven Energy Demand Analytics System

This document provides foundational mandates, architectural context, and a log of key decisions for Gemini CLI. It takes precedence over general workflows.

## 1. Project Overview
A machine learning-based system to predict electricity demand in Spain (ES) using historical load data (ENTSO-E) and meteorological variables (Copernicus ERA5-Land).

### Tech Stack
- **Backend:** Python (FastAPI), Pandas, Scikit-Learn, Optuna, SQLAlchemy.
- **Frontend:** Python (PyQt6) with D3.js integrations.
- **Database:** PostgreSQL (UserDB, ModelDB, PredDB), ELK Stack for logging.
- **Security:** JWT (Bearer tokens), bcrypt (password hashing).
- **Dependency Management:** `pyproject.toml` and `requirements.txt` (located in `Code/energy_prediction_system/`).
- **Testing:** pytest.

## 2. Foundational Mandates
1. **Security First:** NEVER hardcode secrets, API keys, or database URIs. Use `.env` files and `os.environ` or `python-dotenv`.
2. **Data Integrity:** All data ingestion and processing must be idempotent and reproducible. Raw data in `/data/raw/` must NEVER be manually modified.
3. **Automated Testing:** Every new feature or bug fix MUST include unit and/or integration tests in `Code/energy_prediction_system/tests/`.
4. **CI/CD Compliance:** Ensure all changes pass the GitLab CI pipeline (linting, type-checking, tests).
5. **No Prints:** Use the standard `logging` library for all output.

## 3. Engineering Standards
- **Coding Style:** 
  - Follow PEP 8 and use `ruff` for linting/formatting.
  - Use Google-style docstrings for all functions and classes.
  - Mandatory type hinting for function signatures.
  - Use `pathlib.Path` for all filesystem operations.
- **Error Handling:** 
  - Implement robust error trapping with specific exceptions.
  - Use exponential backoff for external API calls (ENTSO-E, CDS).
  - Domain validation is required (e.g., physical limits for temperature/load).
- **Documentation:** Keep `ARCHITECTURE.md` and `DESIGN.md` updated with any structural changes.
- **Dependency Updates:** Add new dependencies to `Code/energy_prediction_system/pyproject.toml` first, then update `requirements.txt`.

## 4. Architectural Patterns
- **Pipe-Filter (ML):** Ingestion -> Raw -> Cleaning -> Processed -> Feature Engineering -> Training.
- **Layered Architecture (App):** User Layer -> Interface (PyQt6) -> Backend (FastAPI) -> Databases.
- **Client-Server:** JSON API communication with Bearer token authentication.

## 5. Directory Mapping
- `Code/energy_prediction_system/src/`: Core logic and pipeline modules.
- `Code/energy_prediction_system/tests/`: Unit and integration tests.
- `Code/energy_prediction_system/pyproject.toml`: Application metadata and configuration.
- `data/raw/`: Immutable external data.
- `data/processed/`: Aligned and cleaned datasets.
- `Architecture/` & `Design/`: Living technical blueprints.

## 6. Decision Log & Recent Context
| Date | Decision | Rationale |
| :--- | :--- | :--- |
| 2026-04-10 | Created `GEMINI.md` | To persist project context and mandates across sessions. |
| 2026-04-10 | Standardized Feature Eng | Added temporal, rolling, lagged, and derived features with PCA. |
| 2026-04-10 | Optimized Rolling Feats | Vectorized Pandas operations to prevent timeout on 52k rows. |
| 2026-04-10 | Corrected Celsius Logic | Updated domain limits and HDD/CDD base temp for Celsius data. |
| 2026-04-10 | Centralized Config | Moved `pyproject.toml` and `requirements.txt` to the app root for Docker. |

---
*Note: This file is a foundational mandate. Update it when significant architectural or procedural decisions are made.*
