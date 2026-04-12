# QUALITY ATTRIBUTES DEFINITION - V2.0

This file contains all QAs for the development of this project.

# Performance

## QA1: Data Pipeline Execution Tracking

* **Source of stimulus:** System Operator and/or Automated Pipeline.

* **Stimulus:** The initiation of data processing workflows (data ingestion, cleaning, feature engineering, and model/evaluation modules).

* **Environment:** Normal operating conditions during a routine data update or model training cycle.

* **Artifact:** The Data Pipeline and Logging Component.

* **Response:** The system executes the requested components and systematically records the start and end times, calculating total execution time for each phase, and writes this data to the system logs.

* **Response measure:** Execution times for 100% of the key components are successfully logged with a timestamp precision of at most 1s.




## QA2: Prediction Latency

* **Source of stimulus:** End User or Client Application.

* **Stimulus:** A request submitted to the system for an energy demand prediction (hourly or daily) based on provided climate variables.

* **Environment:** Local execution environment under normal expected load.

* **Artifact:** The Prediction System and underlying Inference Engine.

* **Response:** The system parses the request, processes the input through the trained machine learning models, and returns the predicted energy demand to the user/application.

* **Response measure:** All prediction requests are processed and successfully returned to the requester within 1.0 seconds.




# Reliability




## QA3: Initial Data Catch-up and Fault Tolerance
* **Source of stimulus:** System Initialization or Live Data Scheduler.

* **Stimulus:** Detection of a data gap exceeding 2 hours between local storage and current API state (e.g., after a long downtime).

* **Environment:** System startup or recovery mode.

* **Artifact:** Live Data Scheduler / Data Pipeline.

* **Response:** The system triggers an asynchronous background sync. If the external API is unreachable, the system times out gracefully, logs the error, and permits the application to continue using the most recent available local data.

* **Response measure:** Successful data retrieval and feature generation occur at a rate of at least 2h of data per 30 seconds of background processing and the application UI and existing Prediction Service remains 100% accessible during the sync attempt.




## QA4: Real-Time Incremental Ingestion

* **Source of stimulus:** Live Data Scheduler (Timer-based).

* **Stimulus:** Arrival of a new hourly timestamp.

* **Environment:** Normal steady-state operation.

* **Artifact:** Live Data Scheduler / Data Pipeline.

* **Response:** The system wakes up a background worker to fetch the single most recent data point, clean it, and update rolling averages.

* **Response measure:** The incremental update completes in under 20 seconds, and the primary Prediction Service experiences 0% interruption (no locks or latency spikes) during the update.


## QA5: Client Network Resilience

* **Source of stimulus:** End User or Client Application.

* **Stimulus:** A request is submitted for an energy demand prediction, but the network connection between the client and the backend server drops or times out.

* **Environment:** Unstable network conditions on the user's end.

* **Artifact:** The Client Application.

* **Response:** The client app detects the unreachable server, prevents the user interface from freezing, and displays a user-friendly "network connection error" message.

* **Response measure:** The network timeout is detected and the UI displays the error state within 3.0 seconds of the request, without crashing the application.




## QA6: Request Rate Limiting

* **Source of stimulus:** End Users or Client Applications.

* **Stimulus:** A sudden massive spike of concurrent energy demand prediction requests arrives, exceeding the server's maximum processing capacity.

* **Environment:** Production environment experiencing extreme user load.

* **Artifact:** The Prediction API Gateway and Load Balancer.

* **Response:** The system actively throttles incoming traffic by processing requests up to its safe threshold. For requests beyond that limit, it instantly returns an HTTP 429 (Too Many Requests) warning to the client to prevent the server's CPU/memory from maxing out and crashing.

* **Response measure:** The server remains online without crashing, processes the accepted predictions within 3 seconds, and successfully issues HTTP 429 rejections for 100% of the excess requests in under 1 second.



## QA7: Pipeline Source Failure

* **Source of stimulus:** Automated Pipeline Scheduler / Data Ingestion Component.

* **Stimulus:** The scheduled task attempts to fetch updated climate/energy data, but the external third-party API is offline or returns a server error.

* **Environment:** Normal internal system operation, but with an unavailable external dependency.

* **Artifact:** Ingestion Module.

* **Response:** The ingestion module detects the API failure, logs the error, safely aborts the current fetch task to prevent system hanging, and triggers a retry mechanism (e.g., exponential backoff) while the rest of the system continues using the last successfully retrieved data.

* **Response measure:** The pipeline gracefully times out the failed fetch attempt within 5.0 seconds, logging the error and retrying 3 times after the first failed attempt to fetch data without halting or crashing the overall system.



## QA8: Graceful Data Degradation

* **Source of stimulus:** Data Pipeline and Storage.

* **Stimulus:** A dataset containing missing, null, or malformed climate/energy values is passed into the data cleaning pipeline.

* **Environment:** Normal data processing and feature engineering phase.

* **Artifact:** The Data Ingestion and Cleaning Component.

* **Response:** The system catches the data anomalies, applies predefined fallback rules, logs a data quality warning, and continues the pipeline execution without throwing unhandled exceptions.

* **Response measure:** 100% of batches with missing/malformed data are processed without causing pipeline crashes, and the system logs the exact number of modified/dropped rows per run.



## QA9: Auto-Recovery from Internal Crash

* **Source of stimulus:** Internal System Error (e.g., unhandled exception, Out of Memory error) or OS-level fault.

* **Stimulus:** The main prediction backend process crashes unexpectedly.

* **Environment:** Normal production environment serving user requests.

* **Artifact:** The Analytics Backend Service and its Process Manager (Docker restart policies).

* **Response:** The process manager detects that the service has failed and automatically restarts the application container. During this downtime, the API Gateway actively returns an HTTP 503 (Service Unavailable) to any incoming requests. The system re-initializes by loading the most recently saved ML model and cached data from disk without requiring manual human intervention.

* **Response measure:** The backend service is successfully restarted, re-loads its models, and is ready to serve new prediction requests within 10 minutes of the initial crash detection. 100% of requests received during the downtime are cleanly rejected with an HTTP 503 status.



# Security


## QA10: Secure Error Handling

* **Source of stimulus:** Unauthenticated User or Automated Scanner.

* **Stimulus:** Submits invalid, malformed, or unauthorized login credentials to the system.

* **Environment:** Public-facing production environment.

* **Artifact:** The Authentication Module.

* **Response:** The system catches the invalid input, rejects the request, logs the failed attempt internally for auditing, and returns a generic, standardized error message to the client, strictly avoiding the exposure of stack traces or system internals.

* **Response measure:** 100% of invalid login attempts receive a generic HTTP 401 (Unauthorized) response, and automated security unit tests verify that zero stack traces or internal implementation details are ever leaked in the payload.




## QA11: Secrets Management

* **Source of stimulus:** Developer and/or data scientist/engineer.

* **Stimulus:** Code is committed to the repository, or a new environment deployment is triggered.

* **Environment:** Development and Production deployment environments.

* **Artifact:** The Source Code Repository and Configuration Management Module.

* **Response:** The system relies exclusively on environment variables injected at runtime for all credentials, API keys, and database URIs. The version control system (via `.gitignore` and pre-commit hooks) rejects any `.env` files or hardcoded secrets.

* **Response measure:** Automated secret scanning tools report 0 violations for hardcoded secrets on every repository commit, and the application successfully boots using 100% dynamically injected environment variables.




## QA12: Input Validation

* **Source of stimulus:** End User, API Client, or Malicious Actor.

* **Stimulus:** Submits a prediction request or authentication payload containing unexpected, out-of-bounds, or potentially malicious strings (e.g., SQL injection attempts, excessively large payloads).

* **Environment:** Normal operational environment.

* **Artifact:** The Prediction Interface and Authentication Layer.

* **Response:** The system parses the input and strictly validates it against predefined schemas (expected data types, value ranges). If validation fails, the system immediately drops the request before it reaches the database or inference engine.

* **Response measure:** 100% of structurally invalid or malicious payloads are rejected with an HTTP 400 (Bad Request) status code in under 1 second, ensuring backend components only process clean data.




## QA13: Brute Force Protection & Auditing

* **Source of stimulus:** Malicious Actor or Automated Bot.

* **Stimulus:** Repeatedly submits invalid login credentials or validation-failing payloads, that is, more than 3 failed attempts within 1 minute.

* **Environment:** Public-facing production environment under active targeted attack.

* **Artifact:** The Authentication Layer.

* **Response:** The system detects the abnormal failure rate, temporarily locks the targeted account or blocks the offending user account, and generates a high-priority security alert in the system logs.

* **Response measure:** The Account lockout is enforced immediately upon breaching the threshold on the 4th attempt for 5 minutes, and the security alert is generated within 1.0 second, preventing further automated guessing.




## QA14: Strict Role-Based Access Control

* **Source of stimulus:** Authenticated Standard User.

* **Stimulus:** Attempts to access a restricted API endpoint without possessing the required "Admin" role.

* **Environment:** Normal operational environment.

* **Artifact:** The API Gateway and Role-Based Access Control (RBAC) Module.

* **Response:** The system verifies the user's token, identifies the lack of required permissions, immediately rejects the request, and logs an unauthorized access attempt.

* **Response measure:** 100% of unauthorized privilege escalation attempts are blocked and return an HTTP 403 (Forbidden) status code in under 1 second, guaranteeing that standard users cannot alter system configurations.



# Usability


## QA15: Navigation Efficiency (3-Click Rule)

* **Source of stimulus:** End User or Admin.

* **Stimulus:** The user needs to access a core system function (e.g., viewing model evaluation metrics or triggering a new prediction).

* **Environment:** Normal operation via the interface, starting from the main hub.

* **Artifact:** The System User Interface (Navigation Menu and Routing).

* **Response:** The interface provides a shallow navigation hierarchy that allows the user to reach any primary functional module without intermediate page loads or nested menus exceeding two levels.

* **Response measure:** 100% of primary functional modules are reachable within 3 distinct clicks from the home dashboard, as verified by a manual UI walk-through test.




## QA16: Data Visualization Interactivity

* **Source of stimulus:** End User (Energy Analyst).

* **Stimulus:** The user initiates a request to view a completed prediction result, triggering the frontend dashboard.

* **Environment:** Post-prediction analysis phase.

* **Artifact:** The Data Visualization Module (Frontend).

* **Response:** The system renders interactive time-series charts of the prediction data, including a comprehensive legend mapped to climate features, and interactive data points.

* **Response measure:** The system renders the complete chart within 1.0 second of the frontend receiving the prediction data payload from the backend API. Additionally, hovering over any data point under 100ms displays a tooltip containing the exact numerical prediction value and the primary climate feature contributing to that point.



# Maintainability



## QA17: Automated Test Coverage and Regression

* **Source of stimulus:** Developer or Data Scientist.

* **Stimulus:** A new feature is added, or a bug fix is implemented in the core logic.

* **Environment:** Local development or CI environment.

* **Artifact:** The Source Code and Automated Test Suite (Unit & Integration).

* **Response:** The system provides a comprehensive test suite that can be executed with a single command, verifying that the new code functions as expected and that existing features remain intact.

* **Response measure:** Automated tests (unit and integration) cover at least 70% of the codebase's core logic, and the full suite completes execution in under 8 minutes, providing feedback on regression errors.




## QA18: Continuous Integration Efficiency

* **Source of stimulus:** Developer.

* **Stimulus:** A code push or Merge Request is submitted to the GitLab repository.

* **Environment:** GitLab CI/CD Pipeline.

* **Artifact:** The CI Pipeline Configuration and Build Environment.

* **Response:** The CI pipeline automatically triggers, installs all necessary dependencies and runs the entire test suite to validate the integrity of the branch.

* **Response measure:** 100% of code pushes to the main or develop branches trigger a CI run, and the pipeline provides a "Success" or "Failure" status within 12 minutes of the push.




## QA19: Traceability and Code Review
**Source of stimulus:** System Maintainer.

**Stimulus:** A developer attempts to push code directly to the "main" production branch.

**Environment:** Git Repository (GitLab/GitHub).

**Artifact:** The Repository Branch Protection Rules.

**Response:** The repository automatically rejects direct pushes to the main branch, forcing the developer to open a Merge Request.

**Response measure:** The main branch protection rules are configured to automatically block 100% of direct pushes to main and strictly require at least 1 approving review before the "Merge" button is unlocked.