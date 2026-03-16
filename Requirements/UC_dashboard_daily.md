# UC: View Daily Forecast Dashboard

**Primary Actor:** User


**Scope/Goal:** 
Allow the user to select a specific date to obtain the forecast of total electricity demand for that day, as well as view the demand projection for the following days and the main factors associated with the forecast.


**Level:** User Goal

**Stakeholders and Interests:**
- User: Wants to check the electricity demand forecast for a specific day and the following days, for planning or analysis purposes.
- Administrador: Wants to ensure that the system correctly calculates the daily forecast and future projections.


**Preconditions:**
1. The user must already be authenticated.
2. The daily regression model is trained and available.
3. The dashboard is accessible.


**Main Success Scenario:**
1. The user accesses the daily dashboard page.
2. The system has a component that allows the user to select a date.
3. The user selects the desired date.
4. The system updates the dashboard and displays the projected value prominently.
5. The system displays visual indicators with the main variables associated with the forecast for that day.
6. The system displays a graph with future projections, showing the demand forecast for the next X days from the selected date.
7. The user can interact with the projection chart to view detailed values ​​for each day.


**Extensions:**
**3a.** Selecting a date:
    - If the user selects a past date, the system informs them that there are actual values ​​available for that day.

**4a.** Data Visualization
    - When the selected date is earlier than the current date, the dashboard displays both the actual value and the projected value for comparison.

**6a.**
    - The system is able to calculate the forecast for the selected day but cannot generate the projection for the following days; the system displays a message on the graph indicating that it was not possible to load the future projection.
    - The system detects potentially anomalous or unrealistic projection values ​​and displays a warning indicating that the projection may be uncertain for that period.