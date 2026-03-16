# UC4: Modeling & Evaluation

**Primary Actor:** Data Scientist with Admin privileges

**Scope/Goal:** Use the optimized and reduced datasets from the Feature Engineering module to train regression models, evaluate their statistical performance, and select the best version for production through a temporal splitting strategy.

**Level:** User Goal Level (Sea Level)

### Stakeholders and Interests
* **Administrator:** Requires a protected interface to trigger training and compare different data variants.
* **Project Supervisor:** Demands the application of rigorous metrics ($R^{2}$, MAE, RMSE) and the absolute prohibition of shuffling in time-series data.

### Preconditions
1.  **Feature Engineering Success:** Datasets with different reduction techniques are available in the `/data/processed/` directory.
2.  **Data History:** Availability of a x-year data history to allow for the x-x-x split.

---

## Main Success Scenario
1.  The system loads the processed electricity load and climate data from the `/data/processed/` directory.
2.  The system applies a **temporal train/test split** to maintain the chronological order of the data; 
3.  For both **Daily** and **Hourly** resolutions, the system executes the training for:
    * **Linear Regression** 
    * **Random Forest** 
4.  The system calculates mandatory performance metrics ($MAE$, $RMSE$, and $R^{2}$) for each model at each resolution. **Additional metrics may be computed as needed for further diagnostic purposes.**
5.  The system performs **residual analysis** to identify potential overfitting.
6.  The system automatically selects the best-performing models (one for daily and one for hourly) based on the validation metrics.
7.  The system persists the winning models and logs the training event, including the username and a timestamp.

---

### Extensions
* **1a. Inconsistency in data within `/data/processed/`:**
    * 1a1. The system detects a failure in the presence of mandatory columns.
    * 1a2. The system terminates the process gracefully, reporting the error in the log.
* **6a. Failure in statistical tests (e.g., insufficient variance):**
    * 6a1. The system uses the $R^{2}$ metric as a tie-breaker and notifies the Administrator in the report.

