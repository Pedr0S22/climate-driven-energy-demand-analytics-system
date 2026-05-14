# TEST CASE DEFINITIONS - V1.1

This file contains all TCs for the development of this project.

## Test Cases for UCs

| Test Case ID | Description | Related UCs | Pre-conditions | Steps | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-UC1** | Verify successful data ingestion from ENTSO-E and Copernicus | UC1 | API credentials configured in .env; system targeting Spain (2020-2025). | 1. Execute ingestion script. 2. Wait for process completion. 3. Check `/data/raw/` subdirectories. | Raw CSV files exist in `weather/` and `energy/` folders; logs in ELK. | – |
| **TC-UC1.1** | Verify graceful handling of ENTSO-E API connection failure | UC1 | Disable network or provide invalid ENTSO-E API key. | 1. Execute ingestion script. 2. Observe script termination. 3. Check ELK logs. | Script terminates cleanly; error logged in ELK; no system crash. | – |
| **TC-UC2** | Verify data cleaning, alignment, and standardization | UC2 | Raw data available in `/data/raw/`. | 1. Execute preprocessing module. 2. Inspect `/data/processed/`. 3. Verify UTC alignment. | `complete_train_data_[hourly\|daily].csv` files created with standardized UTC. | – |
| **TC-UC2.1** | Verify imputation of missing values during cleaning | UC2 | Inject 1 isolated gap and 1 multiple gap in raw energy data. | 1. Run preprocessing. 2. Inspect missing rows in output. | Isolated gap filled via linear interpolation; multiple gaps filled via statistical mean. | – |
| **TC-UC3** | Verify feature engineering and dataset generation | UC3 | Clean data available in `/data/processed/`. | 1. Execute feature engineering module. 2. Check output directory. 3. Verify HDD/CDD columns. | Full, selected, and PCA feature sets created in `feat-engineering/` folder. | – |
| **TC-UC3.1** | Verify dimensionality reduction using PCA | UC3 | Clean data available; high dimensionality detected. | 1. Run feature engineering with PCA extension. 2. Verify `.joblib` transformer. | PCA-reduced dataset generated; `pca_daily.joblib` saved in models. | – |
| **TC-UC4** | Verify model training and evaluation lifecycle | UC4 | Feature sets available in `/data/processed/feat-engineering/`. | 1. Trigger training module. 2. Check `/models/` for binaries. 3. Verify metrics in DB. | Winning LR and RF models saved; metrics (RMSE, R²) stored in PostgreSQL. | – |
| **TC-UC4.1** | Verify tie-breaker logic using R² during evaluation | UC4 | Two models with identical RMSE generated. | 1. Execute training. 2. Observe selection process. | System selects model with higher R²; selection logged in ELK. | – |
| **TC-UC5** | Verify successful user registration | UC5 | System online; email not previously registered. | 1. Enter username, unique email, and valid password. 2. Hit Register. | User created in DB; password hashed; redirected to login. | – |
| **TC-UC5.1** | Verify rejection of registration with existing email | UC5 | Email already exists in `users` table. | 1. Enter existing email. 2. Hit Register. | Registration rejected; error "Email already taken" displayed. | – |
| **TC-UC6** | Verify successful user authentication (Login) | UC6 | Valid user account exists. | 1. Enter registered email and password. 2. Hit Login. | Session granted; redirected to home hub; login logged in ELK. | – |
| **TC-UC6.1** | Verify rejection of invalid login credentials | UC6 | Valid user exists. | 1. Enter correct email but wrong password. 2. Hit Login. | Access denied; generic "Invalid credentials" message; failed attempt logged. | – |
| **TC-UC7** | Verify daily prediction generation with default parameters | UC7 | Authenticated; active daily model in DB. | 1. Request daily prediction. 2. Wait for response. | Forecast values and top 2 drivers returned; success logged in ELK. | – |
| **TC-UC7.1** | Verify daily prediction with custom timeframe | UC7 | Authenticated; active daily model. | 1. Select 5 historical days and 14 forecast days. 2. Hit Predict. | Results returned for the exact custom window specified. | – |
| **TC-UC8** | Verify hourly prediction generation with default parameters | UC8 | Authenticated; active hourly model in DB. | 1. Request hourly prediction. 2. Wait for response. | 12-hour forecast and drivers returned; success logged in ELK. | – |
| **TC-UC8.1** | Verify hourly prediction with custom timeframe | UC8 | Authenticated; active hourly model. | 1. Select 5 historical hours and 24 forecast hours. 2. Hit Predict. | Results returned for the custom hourly window specified. | – |
| **TC-UC9** | Verify administrative model promotion to production | UC9 | Authenticated as Admin; multiple models in DB. | 1. Access Model Management. 2. Select new model. 3. Hit Save. | Model "is_active" updated in DB; confirmation pop-up displayed. | – |
| **TC-UC9.1** | Verify rollback on model configuration save error | UC9 | Authenticated as Admin; simulate DB connection drop. | 1. Attempt to activate model. 2. Hit Save. | Transaction rolls back; error message displayed; previous active model retained. | – |
| **TC-UC10** | Verify daily prediction dashboard rendering and interaction | UC10 | Authenticated; daily prediction available. | 1. Open Daily Dashboard. 2. Hover over chart. | Continuous trend chart rendered; tooltips show precise MWh values. | – |
| **TC-UC10.1** | Verify dashboard update after parameter adjustment | UC10 | Authenticated. | 1. Change forecast horizon in dashboard. 2. Hit Update. | Chart smoothly updates with recalculated prediction values. | – |
| **TC-UC11** | Verify hourly prediction dashboard rendering and interaction | UC11 | Authenticated; hourly prediction available. | 1. Open Hourly Dashboard. 2. Interact with chart. | Hourly trend chart rendered; top 2 drivers visible as indicators. | – |
| **TC-UC11.1** | Verify hourly dashboard update with custom parameters | UC11 | Authenticated. | 1. Change historical context to 5 hours. 2. Hit Update. | Chart updates to show 5 hours of historical data + forecast. | – |
| **TC-UC12** | Verify administrative access to ELK logging dashboard | UC12 | Authenticated as Admin; ELK active. | 1. Select "App Logging" from menu. 2. Observe redirection. | Redirected to Kibana; authenticated session generated; logs visible. | – |
| **TC-UC13** | Verify scenario simulation execution (Daily) | UC13 | Authenticated; models active. | 1. Select Daily. 2. Choose "Heatwave" template. 3. Hit Run Simulation. | Predicted load calculated based on template parameters; logged in ELK. | – |
| **TC-UC13.1** | Verify simulation rejection for invalid physical inputs | UC13 | Authenticated. | 1. Enter temperature = 150°C. 2. Hit Run Simulation. | Validation fails; offending field highlighted; error message displayed. | – |
| **TC-UC14** | Verify secure user logout | UC14 | Authenticated. | 1. Hit Logout button. 2. Verify redirect. | Token cleared; session invalidated; redirected to Login screen. | – |
| **TC-UC15** | Verify scenario simulation result presentation | UC15 | UC13 simulation completed. | 1. View results dashboard. 2. Check summary card. | Predicted MWh prominently shown; template and parameters displayed. | – |

## Test Cases for QAs

| Test Case ID | Description | Related QAs | Pre-conditions | Steps | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-QA1** | Verify precision of pipeline execution tracking | QA1 | Pipeline components active. | 1. Run full pipeline. 2. Inspect ELK logs. | Start/End times logged for 100% of components; precision ≤ 1s. | – |
| **TC-QA2** | Verify prediction API response latency | QA2 | Normal system load. | 1. Submit prediction request. 2. Measure response time. | Response returned in < 1.0 second. | – |
| **TC-QA3** | Verify fault tolerance during background data sync | QA3 | 3h data gap injected. | 1. Start app. 2. Observe background sync. | 2h data/30s rate achieved; UI remains 100% responsive. | – |
| **TC-QA4** | Verify hourly incremental ingestion performance | QA4 | Steady-state operation. | 1. Wait for hourly trigger. 2. Measure update duration. | Incremental update completes in < 20 seconds; 0% API interruption. | – |
| **TC-QA5** | Verify UI resilience during network timeout | QA5 | Active session. | 1. Disable network. 2. Submit request. | "Network connection error" displayed within 10s; app does not crash. | – |
| **TC-QA6** | Verify request rate limiting (429) | QA6 | High load simulation. | 1. Flood API with concurrent requests. | Excess requests rejected with HTTP 429 in < 1s; server remains online. | – |
| **TC-QA7** | Verify ingestion retry logic on API failure | QA7 | External API simulate offline. | 1. Trigger ingestion. 2. Check logs. | 3 retries attempted with exponential backoff; graceful timeout in 5s. | – |
| **TC-QA8** | Verify pipeline processing with malformed data | QA8 | Inject nulls in weather batch. | 1. Run cleaning pipeline. | 100% of batch processed using fallback rules; warning logged. | – |
| **TC-QA9** | Verify auto-recovery from backend process crash | QA9 | Docker environment active. | 1. Kill API process. 2. Monitor recovery. | HTTP 503 during downtime; auto-restart and model reload within 10m. | – |
| **TC-QA10** | Verify generic error handling for security | QA10 | Public interface. | 1. Submit malformed auth payload. | Generic HTTP 401 response; zero stack traces or internal leaks. | – |
| **TC-QA11** | Verify dynamic secrets management | QA11 | Deployment phase. | 1. Check source code. 2. Boot app. | 0 hardcoded secrets found; app uses environment variables. | – |
| **TC-QA12** | Verify rejection of malicious input payloads | QA12 | Prediction interface. | 1. Submit SQL injection string in query. | Request rejected with HTTP 400 in < 1s. | – |
| **TC-QA13** | Verify brute force protection (Lockout) | QA13 | Active targeted attack. | 1. Submit 4 failed logins in 1m. | Account locked for 5 minutes immediately after 4th attempt; alert logged. | – |
| **TC-QA14** | Verify RBAC enforcement for restricted endpoints | QA14 | Standard user account. | 1. Attempt access to `/api/models/activate`. | Request blocked with HTTP 403 in < 1s. | – |
| **TC-QA15** | Verify 3-click navigation efficiency | QA15 | Home dashboard. | 1. Navigate to Model Management (Admin). | Primary modules reachable within 3 distinct clicks. | – |
| **TC-QA16** | Verify data visualization tooltip latency | QA16 | Dashboard rendered. | 1. Hover over chart data point. | Tooltip (value + driver) displayed in < 100ms. | – |
| **TC-QA17** | Verify automated test coverage threshold | QA17 | CI environment. | 1. Run `pytest --cov`. | Code coverage ≥ 70%; full suite executes in < 8 minutes. | – |
| **TC-QA18** | Verify CI/CD pipeline efficiency | QA18 | GitLab repository. | 1. Push code to `main`. | CI triggers automatically; status provided in < 12 minutes. | – |
| **TC-QA19** | Verify branch protection (No direct push) | QA19 | Repository settings. | 1. Attempt direct git push to main. | Push rejected; Merge Request + review required. | – |

## Test Cases for E2E Evaluation

| Test Case ID | Description | Components Involved | Steps | Expected Result | Actual Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-E2E1** | Full Prediction Workflow | Auth, API, Dashboard | 1. Register new user. 2. Login. 3. Navigate to Hourly Dashboard. 4. Change parameters to 5h context/24h forecast. 5. Hit Update. | User successfully sees custom hourly forecast with interactive drivers. | – |
| **TC-E2E2** | Custom Scenario Simulation Workflow | Auth, Simulator, Inference | 1. Login. 2. Open Scenario Simulator. 3. Select "Winter Storm" template. 4. Override temperature to -5°C. 5. Run Simulation. | System renders specific result presentation showing increased demand for winter. | – |
| **TC-E2E3** | Administrative Model Lifecycle | Auth, Model Mgmt, API | 1. Login as Admin. 2. Access Model Management. 3. Compare RF_v2 vs LR_v1 metrics. 4. Activate RF_v2. 5. Request new prediction. | New model is activated without downtime; prediction reflects RF_v2 inference. | – |
