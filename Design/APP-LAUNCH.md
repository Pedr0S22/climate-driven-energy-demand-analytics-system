# Application Launch Guide

This document provides instructions on how to launch the Frontend UI of the Climate-Driven Energy Demand Analytics System.

## Prerequisites

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

To launch the desktop application, execute the `main.py` entry point from within the `Code/energy_prediction_system/src/app/` folder.

```bash
# Run the application
python main.py
```