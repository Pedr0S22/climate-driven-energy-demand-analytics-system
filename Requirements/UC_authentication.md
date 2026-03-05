# UC5: User Authentication - V1.2


**Primary Actor:** User or Admin

**Scope/Goal:** The authentication layer of the Climate-Driven Energy Demand Analytics System. The goal is to mediate and restrict access to the system's protected functionalities based on user roles. The system must verify credentials and grant standard users access to model execution and prediction generation, while granting admins full access, including model training functionality.

**Level:** User Goal

**Stakeholders and Interests:**

* **Standard User:** Needs to seamlessly authenticate to execute models, generate predictions, and access evaluation results.
* **Admin:** Needs to seamlessly authenticate to access all system features, including triggering model training.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user must have previously registered an account with a name, an email and a password.


**Main Success Scenario:**

1. The user opens/accesses the application.

2. The system prompts the user for their email and password credentials.

3. The user inputs their previously registered credentials.

4. The system performs input validation to prevent trivial misuse.

5. The system queries the database to validate the user, hashing the provided password and comparing it against the stored cryptographic hash.

6. The system grants the user access to the app's protected functionalities based on their role.

**Extensions:**

3. a) The user does not have an account:

    * 3a1. The user opts to register rather than log in.

    * 3a2. The system redirects the user to the User Registration flow (UC6 - User Registration).

4. a) Trivial misuse or invalid input format detected:

    * 4a1. The system catches the invalid input during validation.

    * 4a3. The system denies access and prompts the user again for their credentials.

5. a) Invalid login attempt (incorrect password or unrecognized email):

    * 5a1. The system determines the validation check failed in the database.

    * 5a2. The system gracefully rejects the request, ensuring no stack traces or internal implementation details are exposed to the user.

    * 5a3. The system prompts the user again for their credentials.