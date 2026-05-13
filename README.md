# Climate-Driven Energy Demand Analytics System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green.svg)](https://fastapi.tiangolo.com/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.4.0-blue.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8.0-orange.svg)](https://scikit-learn.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![ELK Stack](https://img.shields.io/badge/ELK--Stack-8.x-red.svg)](https://www.elastic.co/elastic-stack)

## Description & Value Proposition

The **Climate-Driven Energy Demand Analytics System** is an end-to-end machine learning platform designed to predict electricity demand in Spain by analyzing the complex relationship between meteorological variables and grid load.

By integrating high-resolution climate data from **Copernicus ERA5-Land** and historical energy data from the **ENTSO-E Transparency Platform**, this system provides:
- **High-Accuracy Forecasting:** Hourly and daily energy demand predictions using regression models (Random Forest, Linear Regression).
- **Climate-Aware Insights:** Dynamic identification of the primary meteorological drivers (e.g., temperature spikes, solar radiation) behind specific demand peaks.
- **Scenario Simulation:** A "What-if" sandbox for analysts to test grid resilience against hypothetical extreme weather events.
- **Automated Data Lifecycle:** A fully reproducible data pipeline that handles everything from ingestion and cleaning to feature engineering and model training.

## Table of Contents
- [Project Status: MVP DEMO](#project-status-mvp-demo)
- [Legal Disclaimer & Objectives](#legal-disclaimer--objectives)
- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Data & Methodology](#data--methodology)
- [Project Structure](#project-structure)
- [Installation (Docker)](#installation-using-docker)
- [User Guide & Workflow](#user-guide--workflow)
- [Authors](#authors)
- [License](#license)

## Project Status: MVP DEMO

This project is currently in its **MVP (Minimum Viable Product) DEMO** phase. While the current implementation focuses on national-level demand for Spain, the architecture is designed for high scalability. Future expansions include:
- **Granular Analysis:** Transitioning from national to regional and city-specific demand models within Spain.
- **International Scaling:** Extending the analytical framework to other European countries by leveraging the standardized ENTSO-E, Copernicus and Open-Meteo data structures.

## Legal Disclaimer & Objectives

This is strictly an **Analytical System**.
- **Disclaimer:** For legal and safety reasons, this system **does not predict catastrophes or force majeure events** (e.g., extreme natural disasters, war, or grid-wide structural failures). It is designed to model standard and seasonal fluctuations driven by climate variables.
- **Objectives:** The primary goal is to provide data-driven insights for grid management, allowing stakeholders to anticipate demand shifts based on temperature, radiation, wind, etc., patterns under normal operational conditions.

## Architecture Overview

The system utilizes a hybrid architectural approach to ensure both scientific reproducibility and high-availability application performance:

1.  **Pipe-Filter Architecture (Data Pipeline):** Ensures a linear, reproducible flow for the ML lifecycle: Ingestion → Raw Storage → Cleaning → Processed Storage → Feature Engineering → Model Training.
2.  **Layered Architecture (Application):** A decoupled 4-tier stack (User, Interface, Backend Services, Databases) that isolates heavy data science workloads from real-time user requests.
3.  **Client-Server Architecture:** A PyQt6-based frontend communicating via RESTful APIs (FastAPI) with a PostgreSQL/ELK backend.

## Key Features

- **Automated Data Pipeline:** Fully automated and reproducible ingestion of over 5 years of historical data with integrated Google Drive cloud synchronization for research continuity.
- **Advanced Feature Engineering:** Goes beyond raw data by calculating temporal lags (L1, L24, L168), rolling climate statistics (mean, std, RMS), and physics-based indicators like Heating/Cooling Degree Days (HDD/CDD) to capture climate inertia.
- **Scenario Simulator:** A sandbox environment where analysts can manually override weather parameters (e.g., "What if we have a 45°C heatwave tomorrow?") to see the predicted impact on the grid instantly.
- **Interactive Visualization Dashboards:** A custom PyQt6 desktop environment with integrated D3.js and Plotly charts, featuring real-time hover tooltips and automated driver identification.
- **Admin Model Management:** A robust governance interface allowing administrators to evaluate new model iterations (RMSE, MAE, R²) and promote them to production with zero downtime.
- **System Observability (ELK):** Integrated ELK Stack (Elasticsearch, Logstash, Kibana) for real-time monitoring of pipeline health, model performance, and user audit trails.

## Data & Methodology

### Data Sources
- **Energy Demand:** Historical grid load data acquired from the **ENTSO-E Transparency Platform**.
- **Meteorological Data:** High-resolution climate variables (Temperature, Solar Radiation, Precipitation, Wind Speed, etc.) from **Copernicus ERA5-Land**.

### Methodology
1.  **Cleaning & Alignment:** Raw data is synchronized to a common UTC grid. Missing values are imputed using rule-based strategies (linear interpolation for isolated gaps, mean of previous observations for larger windows).
2.  **Feature Engineering:** We transform raw signals into predictive features, including temporal decomposition (hour, day, season) and climate inertia indicators (rolling averages and derivatives).
3.  **Modeling:** The system utilizes optimized **Random Forest** and **Linear Regression** models, selected through nested temporal cross-validation with a mandatory 1-year safety gap to prevent data leakage.

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

## Installation using Docker

### Prerequisites
- Docker & Docker Compose installed.
- `.env`, `credentials.json` and `token.json` files with ENTSO-E and Copernicus API keys (placed in `Code/energy_prediction_system/`).

### Setup
1.  **Clone the repository:**
    ```bash
    git clone https://gitlab.com/dei-uc/piacd2026/pl1g1.git
    cd pl1g1
    ```
2.  **How to Run the APP:**
    Navigate to the application root `Code/energy_prediction_system/`:
    ```bash
    cd Code/energy_prediction_system
    ```
    - **Run full application with modifications:**
      ```bash
      docker compose up --build -d
      ```
    - **Run app without modifications:**
      ```bash
      docker compose up -d
      ```
3.  **Run Training Data Pipeline:**
    To run the normal training pipeline with models:
    ```bash
    docker compose --profile tools run pipeline
    ```

## User Guide & Workflow

The application follows a structured workflow designed for both security and efficiency:
1.  **Authentication:** Users must register and log in to access the system.
2.  **Landing Page:** After login, users are presented with a central navigation hub.
3.  **Predictions & Dashboards:** Access real-time hourly or daily demand forecasts with interactive climate insights.
4.  **Simulations:** Perform "What-if" analysis via the Scenario Simulator.

For a detailed walkthrough of all features, please refer to the [Product Documentation (User Guide)](./Design/PRODUCT.md). The full system workflow and use cases are detailed in the [Requirements README](./Requirements/README.md).

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
