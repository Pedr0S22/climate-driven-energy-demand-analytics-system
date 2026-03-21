# QUALITY ATTRIBUTES DEFINITION - V1.1

This file contains all QAs for the development of this project.

# Performance

## QA1: Data Pipeline Execution Tracking

* **Source of stimulus:** System Operator and/or Automated Pipeline.

* **Stimulus:** The initiation of data processing workflows (data ingestion, feature engineering, and model training).

* **Environment:** Normal operating conditions during a routine data update or model training cycle.

* **Artifact:** The Data Pipeline and Logging Component.

* **Response:** The system executes the requested components and systematically records the start and end times, calculating total execution time for each phase, and writes this data to the system logs.

* **Response measure:** Execution times for 100% of the key components (ingestion, feature engineering, and training) are successfully logged with a timestamp precision of at least 1s.



## QA2: Starting App - Initial Data Sync
* **Source of stimulus:** Application Launcher or System Initialization Process.
* **Stimulus:** The application is launched for the first time (or after a cleared cache) and detects that required historical climate and energy data is missing from the local environment.

* **Environment:** Normal operational environment with an active network connection.

* **Artifact:** The Data Synchronization Module (Background Worker) and the User Interface.

* **Response:** The system immediately loads the primary user interface (before login) while delegating the mass data retrieval to a background thread. It displays a non-intrusive loading indicator showing sync progress.

* **Response measure:** The main user interface becomes fully interactive within 5.0 seconds of the app launch, and the background process successfully retrieves 100% of the missing data without causing any UI freezes or blocking the main execution thread.



## QA3: Prediction Latency

* **Source of stimulus:** End User or Client Application.

* **Stimulus:** A request submitted to the system for an energy demand prediction (hourly or daily) based on provided climate variables.

* **Environment:** Local execution environment under normal expected load.

* **Artifact:** The Prediction Interface and underlying Inference Engine.

* **Response:** The system parses the request, processes the input through the trained machine learning models, and returns the predicted energy demand to the user/application.

* **Response measure:** 95% of all prediction requests are processed and successfully returned to the requester within 1.0 seconds.


# Reliability


## QA4: Client Network Resilience

* **Source of stimulus:** End User or Client Application.

* **Stimulus:** A request is submitted for an energy demand prediction, but the network connection between the client and the backend server drops or times out.

* **Environment:** Unstable network conditions on the user's end (e.g., poor Wi-Fi or cellular signal).

* **Artifact:** The Client Application (Prediction Interface).

* **Response:** The client app detects the unreachable server, prevents the user interface from freezing, and displays a user-friendly "network connection error" message.

* **Response measure:** The network timeout is detected and the UI displays the error state within 3.0 seconds of the request, without crashing the application.

## QA5: Request Rate Limiting
* **Source of stimulus:** End Users or Client Applications.

* **Stimulus:** A sudden massive spike of concurrent energy demand prediction requests arrives, exceeding the server's maximum processing capacity.

* **Environment:** Production environment experiencing extreme user load.

* **Artifact:** The Prediction API Gateway and Load Balancer.

* **Response:** The system actively throttles incoming traffic by processing requests up to its safe threshold. For requests beyond that limit, it instantly returns an HTTP 429 (Too Many Requests) warning to the client to prevent the server's CPU/memory from maxing out and crashing.

* **Response measure:** The server remains online without crashing, processes the accepted predictions within 1.5 seconds, and successfully issues HTTP 429 rejections for 100% of the excess requests in under 0.5 seconds.

## QA6: Pipeline Source Failure

* **Source of stimulus:** Automated Pipeline Scheduler / Data Ingestion Component.

* **Stimulus:** The scheduled task attempts to fetch updated climate/energy data, but the external third-party API is offline or returns a server error.

* **Environment:** Normal internal system operation, but with an unavailable external dependency.

* **Artifact:** Ingestion Module.

* **Response:** The ingestion module detects the API failure, logs the error, safely aborts the current fetch task to prevent system hanging, and triggers a retry mechanism (e.g., exponential backoff) while the rest of the system continues using the last successfully retrieved data.

* **Response measure:** The pipeline gracefully times out the failed fetch attempt within 5.0 seconds, logging the error and queuing a retry without halting or crashing the overall analytics engine.



## QA7: Graceful Data Degradation

* **Source of stimulus:** Data Ingestion and Storage.

* **Stimulus:** A dataset containing missing, null, or malformed climate/energy values is passed into the data cleaning pipeline.

* **Environment:** Normal data processing and feature engineering phase.

* **Artifact:** The Data Preprocessing and Cleaning Component.

* **Response:** The system catches the data anomalies, applies predefined fallback rules (e.g., data imputation, or safely dropping unusable rows), logs a data quality warning, and continues the pipeline execution without throwing unhandled exceptions.

* **Response measure:** 100% of batches with missing/malformed data are processed without causing pipeline crashes, and the system logs the exact number of modified/dropped rows per run.



## QA8: Auto-Recovery from Internal Crash

* **Source of stimulus:** Internal System Error (e.g., unhandled exception, Out of Memory error) or OS-level fault.

* **Stimulus:** The main prediction backend or inference engine process crashes unexpectedly.

* **Environment:** Normal production environment serving user requests.

* **Artifact:** The Analytics Backend Service and its Process Manager (Docker restart policies).

* **Response:** The process manager detects that the service has failed, automatically restarts the application container/process, and the system re-initializes by loading the most recently saved ML model and cached data from disk without requiring manual human intervention.

* **Response measure:** The backend service is successfully restarted, re-loads its models, and is ready to serve new prediction requests within 1 minute of the initial crash detection.