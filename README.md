# Climate-Driven Energy Demand Analytics System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

## Description & Value Proposition

The **Climate-Driven Energy Demand Analytics System** is an end-to-end machine learning platform designed to predict electricity demand in Spain by analyzing the complex relationship between meteorological variables and grid load.

By integrating high-resolution climate data from **Copernicus ERA5-Land** and historical energy data from the **ENTSO-E Transparency Platform**, this system provides:
- **High-Accuracy Forecasting:** Hourly and daily energy demand predictions using regression models (Random Forest, Linear Regression).
- **Climate-Aware Insights:** Dynamic identification of the primary meteorological drivers (e.g., temperature spikes, solar radiation) behind specific demand peaks.
- **Scenario Simulation:** A "What-if" sandbox for analysts to test grid resilience against hypothetical extreme weather events.
- **Automated Data Lifecycle:** A fully reproducible data pipeline that handles everything from ingestion and cleaning to feature engineering and model training.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Installation (Docker)](#installation-using-docker)
- [Usage](#usage)
- [Authors](#authors)
- [License](#license)

## Architecture Overview

The system utilizes a hybrid architectural approach to ensure both scientific reproducibility and high-availability application performance:

1.  **Pipe-Filter Architecture (Data Pipeline):** Ensures a linear, reproducible flow for the ML lifecycle: Ingestion → Raw Storage → Cleaning → Processed Storage → Feature Engineering → Model Training.
2.  **Layered Architecture (Application):** A decoupled 4-tier stack (User, Interface, Backend Services, Databases) that isolates heavy data science workloads from real-time user requests.
3.  **Client-Server Architecture:** A PyQt6-based frontend communicating via RESTful APIs (FastAPI) with a PostgreSQL/ELK backend.

## Key Features

- **Automated Data Pipeline:** Reproducible ingestion of 6 years of historical data (2020-2025) with integrated Google Drive backups.
- **Advanced Feature Engineering:** Calculates rolling climate averages, temporal lags, and physics-based indicators like Heating/Cooling Degree Days (HDD/CDD).
- **Interactive Dashboards:** Visualizes demand trends using D3.js integrated within a PyQt6 desktop environment, supporting real-time hover tooltips and driver identification.
- **Scenario Simulator:** Allows users to manually define weather parameters to simulate grid impact without relying on live API data.
- **Admin Model Management:** A dedicated interface for administrators to evaluate model metrics (MAE, RMSE, R²) and promote new models to production on-the-fly.
- **Observability (ELK Stack):** Centralized logging and monitoring via Elasticsearch, Logstash, and Kibana for total system transparency.

## Project Structure
```text
├── Architecture/          # High-level architectural blueprints and diagrams
├── Code/
│   ├── calculator/        # Arithmetic operations and unit tests module
│   ├── energy_prediction_system/ # Main Application Root (pyproject.toml, requirements)
│   │   ├── src/           # Core logic (data_pipeline, backend, frontend)
│   │   ├── tests/         # Unit and integration tests
│   │   ├── data/          # Local data storage (raw, processed, aligned)
│   │   └── models/        # Trained model binaries and feature engineering artifacts
│   └── poems/             # (Project-specific artifacts)
├── Design/                # Low-level design docs, API specs, and Dev "How-To" guides
├── Management/            # Project management, team profiles, and milestones
├── Requirements/          # Official Use Cases and Quality Attributes
└── Testing/               # Automated test reports and test case definitions
```

## Installation using Docker [TODO]

> **`IMPORTANT:`**
>This section is under development. Ensure you have Docker and Docker Compose installed.

### Prerequisites
- Docker Desktop
- `.env`, `credentials.json` and `token.json` files with ENTSO-E and Copernicus API keys (see `Design/DESIGN.md` for template).

### Setup (TODO) - [TODO] (usage of docker hub)
1.  **Clone the repository:**
    ```bash
    git clone https://gitlab.com/dei-uc/piacd2026/pl1g1.git
    cd pl1g1
    ```
2.  **Configure environment variables:**
    - Create a `.env` file in `Code/energy_prediction_system/`.
3.  **Build and run the containers:**
    ```bash
    # TODO: Define final docker-compose structure
    docker-compose up --build
    ```

## Usage [TODO]

### 1. Data Pipeline (CLI)
To run the automated pipeline, use the provided scripts in the `src/data_pipeline/` directory.
```bash
# Example: Ingest data
python Code/energy_prediction_system/src/data_pipeline/ingestion.py
```

### 2. Application (GUI)
Launch the PyQt6 interface to access predictions and simulations.
```bash
# TODO: Define main entry point for the desktop app
python Code/energy_prediction_system/src/main_app.py
```

## Authors
Meet the team behind this product:
*   **Pedro Silva** (@Pedr0S22)
*   **Beatriz Fernandes** (@2023215703BeaFernandes)
*   **Francisca Mateus** (@franciscamateusPt05)
*   **Ramyad Raadi** (@Ramyad20)
*   **Rebeca Power** (@reberapower1)

For more details, visit our [Team Profiles](./Management/profiles).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
