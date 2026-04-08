# Requirements Folder

In this readme you can find all information related to the project requirements, including the UCs, QAs and TCs.

# Use Cases

Below there is a short presentation on what are the UCs, their numeration and how their related:

### Data Pipeline
- UC1 - Data Ingestion from exterior sources
- UC2 - Data cleaning, tranformation and alignment
- UC3 - Feature Engineering
- UC4 - Modeling and Evalutation

### Application
- UC5 - User registration
- UC6 - User authentication

    ### Options

- UC7 - Daily prediction generation
    - UC10 - Daily prediction dashboard

- UC8 - Hourly prediction generation
    - UC11 - Hourly prediction dashboard

    ### Admin Only Options
- UC9 - Admin model management
- UC12 - App logging



# Quality Attributes

To complement the Use Cases, we defined Quality Attributes that this software must obey. Below, we have the main topic QAs followed by their specific QAs:

### Performance (Latency & Tracking)

- QA1: Data Pipeline Execution Tracking
- QA2: Starting App - Initial Data Sync
- QA3: Prediction Latency

### Reliability (Fault tolerance & Recovery)

- QA4: Client Network Resilience
- QA5: Request Rate Limiting
- QA6: Pipeline Source Failure
- QA7: Graceful Data Degradation
- QA8: Auto-Recovery from Internal Crash

### Security (Auth & Validation)

- QA9: Secure Error Handling
- QA10: Secrets Management
- QA11: Input Validation
- QA12: Brute Force Protection & Auditing
- QA13: Strict Role-Based Access Control

### Usability (UX & Viz)

- QA14: Navigation Efficiency (3-Click Rule)
- QA15: Interface Familiarity and Learnability
- QA16: Data Visualization Clarity

### Maintainability (CI/CD & Testing)

- QA17: Automated Test Coverage and Regression
- QA18: Continuous Integration Efficiency
- QA19: Traceability and Code Review

### Functionality (E2E Completeness)

- QA20: E2E Completeness



# Test Cases

TODO