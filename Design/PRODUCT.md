# Product Documentation | User Guide: Climate-Driven Energy Demand Analytics System

This document provides a comprehensive guide to the features, objectives, and operational workflows of the Climate-Driven Energy Demand Analytics System. It is designed to help users and analysts leverage the system's full potential for grid demand forecasting and resilience testing.

## 1. System Possibilities & Value
The system transcends simple forecasting by offering a multi-layered analytical environment. Key possibilities include:
- **Precision Load Balancing:** Anticipate intraday demand spikes to optimize energy distribution.
- **Climate Sensitivity Analysis:** Quantify exactly how much a 1°C increase in temperature or a 10% change in solar radiation affects the national grid.
- **Risk Mitigation:** Test "black swan" weather events eltric demand in Spain in a safe, simulated environment without risking grid stability.
- **Scalable Infrastructure:** Transition seamlessly from national analysis to regional or international demand modeling.

## 2. Functional Objectives

### 2.1. Hourly Predictions
- **Primary Goal:** Provide short-term, high-resolution foresight for intraday grid operations.
- **Use Case:** Managing rapid demand shifts during peak hours (e.g., lunch-time surges or evening cooling spikes).
- **Output:** A 24-hour forecast horizon with identified top 2 drivers (e.g., "Time of Day" and "2m Temperature").

### 2.2. Daily Predictions
- **Primary Goal:** Support medium-term resource planning and seasonal trend analysis.
- **Use Case:** Anticipating weekly energy requirements for fuel procurement or maintenance scheduling.
- **Output:** A 14-day forecast horizon showing total daily consumption (MWh) and primary drivers (e.g., "HDD" and "Lagged Weekly Load").

### 2.3. Scenario Simulations ("What-If" Analysis)
- **Primary Goal:** Evaluate model sensitivity and grid resilience under non-live, hypothetical conditions.
- **Use Case:** Stress-testing the system against extreme heatwaves or winter storms that haven't occurred in the recent historical data.
- **Output:** Instantaneous demand prediction for a synthesized feature vector, comparing baseline templates with manual overrides.

## 3. Data Handling Lifecycle
The system ensures data integrity through a strictly controlled pipeline:
1.  **Ingestion:** Reproducible retrieval from ENTSO-E (Load) and Copernicus (Climate) with 31-day windows for real-time parity.
2.  **Cleaning & Alignment:** Automatic UTC synchronization, 15-minute grid alignment, and rule-based imputation (Linear/Statistical Mean).
3.  **Feature Engineering:** Transformation of raw signals into physics-based features (HDD, CDD, RMS, Rolling Std) and temporal lags.
4.  **Real-Time Sync:** Background workers fetch the most recent data points every 30 minutes, ensuring the "Real-Time" dashboard never becomes stale.
5.  **Persistence:** Raw data is backed up to Google Drive, while processed artifacts and models are versioned on disk.

## 4. Operational User Guide

### 4.1. How to Run Predictions
Users can access predictions via the **Daily** or **Hourly Options** after **Registratation** and **Login**:
1.  **Select Context:** Choose how many historical points to display (Context Window) to see recent trends.
2.  **Select Horizon:** Define the forecast length (e.g., next 12 hours or next 7 days).
3.  **Identify Drivers:** Observe the visual indicators for the "Top 2 Drivers." If "t2m" is a driver, the current demand is being heavily influenced by temperature.
4.  **Interactive Tooltips:** Hover over any chart point to see the exact MWh value and the specific variable contributing to that point.

### 4.2. How to Run Simulations
The **Scenario Simulator** allows for deep-dive analysis without relying on live data:
1.  **Choose Resolution:** Toggle between Daily and Hourly simulation modes.
2.  **Select a Template:** Choose a Base Scenario (see below) to pre-fill the feature vector.
3.  **Apply Overrides:** Manually adjust primary drivers like Temperature, Pressure, or Precipitation.
    - *Note:* The system enforces physical limits (e.g., Temperature -40°C to 55°C) to prevent nonsensical results.
4.  **Execute:** Hit "Run Simulation" to see the predicted demand and the context summary card.

## 5. Simulation Templates
The system includes **16 pre-defined templates** (4 Weather States x 2 Frequencies x 2 Seasonal Variants) to provide a robust starting point for simulations:

| Weather State | Description | Typical Use Case |
| :--- | :--- | :--- |
| **Average** | Baseline conditions for the selected season. | Comparing "normal" demand against deviations. |
| **Rainy** | Low solar radiation, high humidity. | Testing demand shifts when solar generation is low. |
| **Storm** | High pressure/wind, low temperatures. | Analyzing heating stress on the grid. |
| **Heatwave** | Sustained extreme high temperatures. | Stress-testing cooling demand and thermal inertia. |

Each state exists in both **Hourly** (capturing diurnal cycles) and **Daily** (capturing total energy volume) resolutions, adapted for **Summer** and **Winter** baselines to account for seasonal demand variations.

---
*For detailed use case steps, refer to `Requirements/USE_CASES.md`. For technical API details, see `Design/DESIGN.md`.*
