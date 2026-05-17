# Application Launch Guide

This document provides instructions on how to launch the Frontend UI of the Climate-Driven Energy Demand Analytics System.

## Pre-requisites

Before running the application, make sure your Python environment has the necessary dependencies installed.

```bash
# From the project root (/Code/energy_prediction_system)
pip install -r requirements.txt
```

If you intend to run or modify tests, install the development dependencies instead:

```bash
pip install -r requirements-dev.txt
```

*(Note: These files ensure that all frontend-specific dependencies are properly set up).*

## Launching the Application

To launch the desktop application, you must ensure all backend is working with docker. For that, follwo these steps:

1. Navigate to the application root `Code/energy_prediction_system/`:
    ```bash
    cd Code/energy_prediction_system
    ```
2. Run Backend with docker:
    ```bash
    docker compose up --build -d
    ```

After this process, execute the `main.py` entry point from within the `Code/energy_prediction_system/src/app/` folder.

1. Navigate to the frontend application root `Code/energy_prediction_system/src/app/`:
    ```bash
    cd Code/energy_prediction_system/src/app
    ```

2. Run Frontend in the terminal:
    ```bash
    python main.py
    ```