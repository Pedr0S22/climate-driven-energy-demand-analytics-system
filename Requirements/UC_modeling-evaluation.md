# UC: Modeling & Evaluation

**Primary Actor:** Data Scientist with Admin privileges

**Scope/Goal:** Use the optimized and reduced datasets from the Feature Engineering module to train regression models, evaluate their statistical performance, and select the best version for production through a temporal splitting strategy.

**Level:** User Goal Level (Sea Level)

### Stakeholders and Interests
* **Administrator:** Requires a protected interface to trigger training and compare different data variants.
* **Project Supervisor:** Demands the application of rigorous metrics ($R^{2}$, MAE, RMSE) and the absolute prohibition of shuffling in time-series data.

### Preconditions
1.  **Authentication:** The Administrator is authenticated in the system.
2.  **Feature Engineering Success:** Datasets with different reduction techniques are available in the `/data/processed/` directory.
3.  **Data History:** Availability of a 7-year data history to allow for the 5-1-1 split.

---

### Main Success Scenario (Basic Flow)
1.  The authenticated Administrator triggers the modeling and selection pipeline.
2.  The system loads the available datasets in the `/data/processed/` directory, which contain the different dimensionality reduction variants.
3.  The system applies a **TVT (Train-Validation-Test)** temporal splitting strategy:
    * **Train (5 years) and Validation (1 year):** Used for model adjustment and selection through temporal K-fold Cross-Validation (in blocks such as seasonal, semi-annual, or annual).
    * **Test (1 year):** Final isolated block for real-world performance evaluation.
4.  For each reduced dataset, the system executes the training for **Linear Regression** and **Random Forest**.
5.  The system calculates the mandatory metrics: **MAE**, **RMSE**, and **$R^{2}$**.
6.  The system applies statistical tests to validate if the error differences between models and reductions are significant.
7.  The system automatically selects the best model and validates it against the final test block.
8.  The system persists the winning model and records a detailed log.

---

### Extensions
* **1a. User without Administrator privileges:**
    * 1a1. The system denies access to the training functionality and logs the attempt.
* **2a. Inconsistency in data within `/data/processed/`:**
    * 2a1. The system detects a failure in the presence of mandatory columns.
    * 2a2. The system terminates the process gracefully, reporting the error in the log.
* **6a. Failure in statistical tests (e.g., insufficient variance):**
    * 6a1. The system uses the $R^{2}$ metric as a tie-breaker and notifies the Administrator in the report.

---

### Acceptance Criteria
* **Security:** Access to the training and model selection function is restricted to Administrators.
* **Integrity:** The data split strictly respects chronology (**no random shuffling**).
* **Performance:** Training execution time must be measured, and the final prediction response must be **< 1s**.
* **Quality:** MAE, RMSE, and $R^{2}$ metrics must be reported, and a **residual analysis** must be performed.