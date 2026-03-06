# UC: analytics dashboard - V1.1
**Primary Actor**:
Developer

**Scope/Goal**: The goal is to present a dashboard to an authorized user, consolidating results from multiple background processes (e.g: prediction) into a single location to facilitate data queries and the visualization of key interests.

**Level**:
User Goal

**Stakeholders and Interests**:
**Data cientist/engineer**: Wants to quickly consult information through a simple and intuitive interface, without running manual scripts.

**Security administrator**: Needs to ensure that only users who passed the authentication (UC5) can view the data.

**Developer**: Wants to ensure that the complex logic of the backend is presented clearly and correctly to the end-user.

**Preconditions**:
1. The user has successfully logged into the system.

2. The entire data pipeline, from automated ingestion and cleaning to the predictive model execution, is fully functional.

**Main Success Scenario**:
1. The use case starts when the authorized user accesses the Dashboard section.

2. The system presents a unified view containing information about the data and system status, such as:

    - Climate-Energy correlations and relevant features: Visualizations of how weather variables impacted past demand.

    - Forecast summaries: Expected energy peaks and trends for the upcoming period.

    - Pipeline status: Information on the last successful data ingestion and model training.

    - Last query/request history: a dedicated visualization/section showing the parameters (date range,variables) of the most recent query performed by the user.

3. The system provides filtering and query tools, allowing the user to isolate specific dates or climate conditions.

4. The user reviews the integrated information to gain insights into the energy-climate relationship.

5. The system logs the execution time for the operation chosen by the user.

Extensions:

2.  a) No previous query history found:

    * 2a1. The system displays a "no history found" message. 

    * 2a2. The system suggests a default visualization (e.g., the last 24 hours).

    b) No data available to display:
    
    * 2b1. The system informs the user that the pipeline needs to be executed before results can be shown.

    * 2b2. The system may provide a button to trigger the data update process if the user has the required permissions.

3.  a) Incompatibility with current data:

    * 3a1. If the last query used a date range that isn´t available in the memory or cache, the system notifies the user and suggests the nearest available period.