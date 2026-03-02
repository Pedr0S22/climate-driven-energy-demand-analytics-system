# UC5: User Authentication - V1.1 - Training Functionality Question


**Primary Actor:** Developer

**Scope/Goal:** The authentication layer of the Climate-Driven Energy Demand Analytics System. The goal is to mediate and restrict all access to model execution, prediction generation, (`??????` and training functionality `??????`). The user must be logged in to acess the app.

**Level:** User Goal

**Stakeholders and Interests:**


* **User:** Needs to seamlessly authenticate to trigger `??????`model training `??????`, generate predictions, or access evaluation results.


* **Security Administrator:** Needs assurance that passwords are not stored in plaintext , are securely hashed using an appropriate cryptographic function , and that all authentication attempts are reliably logged.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user must have previously registered an account with a username and a password.


**Main Success Scenario:**

1. The user opens/accesses the application.

2. The system prompts the user for their username and password credentials.

3. The user inputs their previously registered credentials.

4. The system performs input validation to prevent trivial misuse.

5. The system queries the database to validate the user, hashing the provided password and comparing it against the stored cryptographic hash.

6. The system logs the successful authentication attempt, recording the timestamp and the username.

7. The system grants the user access to the app's protected functionalities.

**Extensions:**

3. a) The user does not have an account:

    * 3a1. The user opts to register rather than log in.

    * 3a2. The system redirects the user to the registration flow, where they provide a username and a password of at least eight characters and at most 20.

    * 3a3. Once registered, the user accesses the login section of the app

    * 3a4. The flow returns to step 2.

4. a) Trivial misuse or invalid input format detected:

    * 4a1. The system catches the invalid input during validation.

    * 4a2. The system logs the attempt.

    * 4a3. The system denies access and prompts the user again * for its credentials.

5. a) Invalid login attempt (incorrect password or unrecognized username):

    * 5a1. The system determines the validation check failed in the database.

    * 5a2. The system gracefully rejects the request, ensuring no stack traces or internal implementation details are exposed to the user.

    * 5a3. The system logs the failed authentication attempt, logging the timestamp and username.

    * 5a4. The system prompts the user to try again.

    * 5a5. The system prompts the user again for its credentials.