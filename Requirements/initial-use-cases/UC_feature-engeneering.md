# UC3: Feature Engeneering - V1.5

**Primary actor**:
Data Scientist/Developer

**Scope/Goal**:
Transform the clean and sincronized data into relevant predictive features (temporal, lagging, rolling, and advanced) to feed the modeling component, from which:


**1. Mandatorty**:
- **Temporal features**: hour, day, season;
- At least one **rolling climate feature**;
- At least one **lagged demand feature**.


**2. Optional**:
- Derived features.

**Level**:
User goal.

**Stakeholders and Interests**:

* **Data cientist**: Expects to obtain relevant features that capture trends, seasonality, and complex climate-energy relationships to improve model performance.

* **Data Engineer**: Expects an efficient, modular transformation process that is well-integrated into the system's pipeline.

* **Validator**: Aims to ensure that errors such as data leakage do not occur and that temporal integrity is maintained.

**Preconditions**:
1. The Data Cleaning and Alignment stage has been successfully completed.

2. Synchronized data is available in the `/data/processed/ `directory.

3. The system has validated that all required columns and timestamps are present and reliable.

**Main Success Scenario**:
1. The use case starts when the feature engineering module is activated, which occurs once the data cleaning stage is completed;

2. The system loads the data available in the `/data/processed/` directory;

3. The system extracts temporal features, including hour of the day, day of the week, and seasonal indicators.

4. The developer defines the window size and the overlap, constrained by the dataset timestamps, to ensure the rolling windows are physically meaningful;

5. The system extracts rolling climate features, such as:
    - mean;
    - median;
    - standard deviation;
    - variance;
    - root mean square;
    - average derivatives;
    - skewness, kurtosis, IQR, zero crossing rate, mean crossing rate, and pairwise correlation;

6. The system extracts lagged demand features, such as:
    - L1 Load: Electrical load one hour ago;
    - L24 Load: Load one day ago;
    - L168 Load: Load one week ago;

7. The system derives new features from the data to provide additional analytical depth, such as:
    - Temperature Anomalies: Deviation from seasonal/monthly means;
    - Climatic Indicators: Heating Degree Days (HDD) or Cooling Degree Days (CDD);
    - Heatwave/Coldwave Flags: Binary indicators based on persistent extreme temperatures.

8. The system validates that the features obtained don't include invalid values generated during the feature extraction process.

9. The system measures and logs the execution time.

10. The system logs the total feature count.

11. The system saves the full feature set as the primary dataset for the predictive model, ensuring the output format is compatible with the model training pipeline.

**Extensions**:

8. a) Minor domain inconsistencies detected (e.g., a few records with values that do not align with physical constraints):
    * 8a1. The system handles them by dropping or imputing the affected rows to maintain dataset quality.

    b) Critical domain-context errors detected (e.g., widespread anomalies where feature values are physically implausible):
    * 8b1. The system logs a domain consistency error and the process terminates to prevent training a model on nonsensical data.

    * 8b2. The developer must review the previous extraction logic or source data to identify the source of the contextual mistake.

10) a) High dimensionality detected:

    * 10a1. The system performs feature selection (e.g., Fisher Score, ReliefF) to identify the most predictive variables.

    * 10a2. The system performs dimensionality reduction (e.g., PCA) to compress information.

    * 10a3. The system generates and labels these new dataset versions.

    * 10a4. The system saves each resulting dataset version as a separate file to allow for comparative training and evaluation in the next stage.

    * 10a4. The system ensures these new versions are compatible with the model training pipeline.
