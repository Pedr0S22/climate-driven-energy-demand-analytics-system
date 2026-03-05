# UC2:Data Cleaning and Alignment

**Primary Actor:** Developer

**Scope/goal:** The objective is to clean, validate, align, and standardize the datasets to a common temporal resolution, ensuring data integrity, robustness, and quality before the training phase. The processed data must be stored in /data/processed/.

**Level:** User goals

**Stakeholders/Interests:** 
- User: Wants to ensure the system uses clean and consistent data to generate reliable forecasts.
- Developer/ Data Analyst: Require reliable and consistent data to ensure robustness in the models and subsequent steps.
- Administrador: Needs assurance that raw data remains untouched and that processed data is stored separately under /data/processed/.

**Preconditions:**
- Data must be located in the correct folders from the previous step;
- The /data/processed/ folder must exist;
- Datasets must contain the mandatory columns required for this process (timestamp, electricity load, temperature, solar radiation, wind speed, precipitation).



**Main Success Scenario:**
1. The use case begins when the data preprocessing module is executed.
2. The system loads raw data from /data/raw/weather/ and /data/raw/energy/.
3. The system converts timestamps to the UTC standard and checks for any timezone inconsistencies.
4. The system handles missing values in the following variables: temperature, wind speed, solar radiation, electricity load, and precipitation.
5. The system detects outliers using the IQR method for all variables except electricity load. For each detected value, the system verifies whether it is plausible according to the predefined limits.
6. The system aggregates data every hour, averaging temperature, wind, radiation, and precipitation; for electrical charge, we use the maximum value for that interval.
7. The system merges both datasets into a single dataset and saves the processed data in the /data/processed/ folder.

**Extensions:**
3. a) The system detects that not all expected timestamps (15-minute intervals) exist:
    * If any time value is missing, what we do is, since the data is for 15 minutes, we add a line for the timestamp that was supposed to be there, and the remaining variables are marked as missing values ​​for later processing.

4. a) Missing Values Detected
    1.  If there is 1 isolated missing value per hour:
        - The system applies linear interpolation between the previous and the next value.
    2. If there is more than 1 missing value within a 1-hour interval:
        - The system estimates missing values using statistical methods based on nearby valid observations.
        - For solar radiation, the system considers whether the timestamp corresponds to daytime or nighttime when estimating the value.
        - For precipitation, the system evaluates surrounding observations to determine whether the value should remain zero or be estimated from nearby valid data.

5. a) Outlier detected by IQR
    1. If the value is outside the limits:
        - The system replaces the value using statistical estimates based on nearby valid observations, taking into account the characteristics of each variable;
    2. If the value is outside the IQR but within plausible limits:
        - The system retains the value, considering it a possible outlier.
    
6. a) The timestamps are not all the same time:
    * If there are timestamps that do not exactly match xx:00, xx:15, xx:30, or xx:45:
        - The system adjusts them to the nearest 15-minute interval before time aggregation.
    
