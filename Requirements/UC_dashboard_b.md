# UC: View Hourly Forecast Dashboard

**Primary Actor:** User


**Scope/Goal:** 
Allow the user to select a specific date and time to obtain the electricity demand forecast for that period, as well as generate projections for the following hours, presenting the results visually on the dashboard.


**Level:** User Goal

**Stakeholders and Interests:**
- User: Wants to get forecasts for the selected specific time as well as for the following hours, and view the results clearly.
- Administrador: Wants to ensure that the hourly forecast model works correctly and that the generated predictions are reliable.


**Preconditions:**
1. The user must already be authenticated.
2. The hourly forecast model is trained and available.
3. The dashboard is accessible.


**Main Success Scenario:**
1. The user accesses the hourly dashboard.
2. The system presents a component to select date and time.
3. The user selects the desired date and time.
4. The system displays the predicted value as a visual indicator on the dashboard.
5. The system shows the projection for the next X hours in a chart
6. The user can interact with the projection chart to view detailed values ​​for each hour.

**Extensions:**
**3a** Selected Hour
    - The user selected a time prior to the current time, and the system indicates that actual values are available for that time/day.
**4a** Data visualization
    - If the user selects a time prior to the current time, the system displays both the actual value and the forecast for that time.
**5a.** Future Projection Failure
    - The system is unable to display the forecast for the following hours and shows a message indicating that the future projection cannot be loaded.
    - If the projected values ​​for the next few hours appear anomalous, the system displays a warning indicating that the forecast may be uncertain for that period.