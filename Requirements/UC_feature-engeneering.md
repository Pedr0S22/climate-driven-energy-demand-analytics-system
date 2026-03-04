# UC5: Feature Engeneering - V1.1
Feature engineering

**Primary actor**: 
Data Scientist/Developer

**Scope/Goal**:
Transform the clean and sincronized data into relevant predictive features, from which:


Mandatorty:
- Temporal features: hour, day, season;
- Al least one rolling climate feature;
- At least onde lagged demand feature.


Opcional:
- Derived features.

**Level**:
User goal.

**Stakeholders and Interests**:

Data cientist: Expects to obtain relevant features that can catch trend or other aspects that improve predictive model performance.

Data Engineer: Expects the process of transforming data into relevant features to be efficient and well integrated into the system’s pipeline.

Validator: Aims to ensure that errors such as data leakage do not occur.

**Preconditions**:
The Cleaning and Alignment stage resulted in energy data and weather observations that are synchronized, contain no missing or duplicate records, include the required columns, and where all observations are reliable.

These data are available in the /data/processed/ directory. 

**Main Success Scenario**: 
1. The use case starts when the feature engineering module is activated, which occurs once the data cleaning stage is completed;

2. The system loads the data available in the /data/processed/ directory;

3. The system extracts temporal features: hour of the day, day of the week, and season of the year;

4. The developer defines the window size and the overlap, constrained by the dataset timestamps;

5. The system extracts rolling climate features, such as: 
- mean; 
- median; 
- standard deviation; 
- variance; 
- root mean square;
- average derivatives;
- skewness, kurtosis, IQR, zero crossing rate, mean crossing rate, and pairwise correlation;

6. The system extracts lagged demand features; 

7. The system derives new features from the data, such as:
- L1 Load: Electrical load one hour ago;
- L24 Load: Load one day ago;
- L168 Load: Load one week ago;

- It can perform the same calculations for climate variables;
8. Someone validates that the feature set does not include invalid values generated during the feature extraction process.

9. The system evaluates which features are most relevant using dimensionality-reduction methods.

10. The system saves the final feature set as a dataset that can feed the predictive model.


