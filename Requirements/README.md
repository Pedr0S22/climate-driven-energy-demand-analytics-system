# Requirements Folder

In this README, you can find all information related to the project requirements, including the UCs and the QAs. The TCs, that test the UCs and QAs, are found in the [Testing folder](../Testing/TEST_CASES.md).

# Use Cases

Below there is a short presentation on what are the UCs, their numeration and how their related:

### Data Pipeline
- UC1 - Data Ingestion from exterior sources
- UC2 - Data cleaning, transformation and alignment
- UC3 - Feature Engineering
- UC4 - Modeling and Evaluation

### Application
- UC5 - User registration
- UC6 - User authentication
- UC14 - User logout

    ### Options

- UC7 - Daily prediction generation
    - UC10 - Daily prediction dashboard

- UC8 - Hourly prediction generation
    - UC11 - Hourly prediction dashboard
- UC13 - Scenario simulation

    ### Admin Only Options
- UC9 - Admin model management
- UC12 - App logging



# Quality Attributes

To complement the Use Cases, we defined Quality Attributes that this software must obey. Below, we have the main topic QAs followed by their specific QAs:

### Performance (Latency & Tracking)

- QA1: Data Pipeline Execution Tracking
- QA2: Prediction Latency

### Reliability (Fault tolerance & Recovery)

- QA3: Initial Data Catch-up and Fault Tolerance
- QA4: Real-Time Incremental Ingestion
- QA5: Client Network Resilience
- QA6: Request Rate Limiting
- QA7: Pipeline Source Failure
- QA8: Graceful Data Degradation
- QA9: Auto-Recovery from Internal Crash

### Security (Auth & Validation)

- QA10: Secure Error Handling
- QA11: Secrets Management
- QA12: Input Validation
- QA13: Brute Force Protection & Auditing
- QA14: Strict Role-Based Access Control

### Usability (UX & Viz)

- QA15: Navigation Efficiency (3-Click Rule)
- QA16: Data Visualization Interactivity

### Maintainability (CI/CD & Testing)

- QA17: Automated Test Coverage and Regression
- QA18: Continuous Integration Efficiency
- QA19: Traceability and Code Review