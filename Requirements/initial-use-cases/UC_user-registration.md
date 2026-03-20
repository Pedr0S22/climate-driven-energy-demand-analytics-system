# UC6: User Registration - V1.2

**Primary Actor:** User

**Scope/Goal:** The user management module of the Climate-Driven Energy Demand Analytics System. The goal is to allow new users to register an account with a username, email and password so they can later authenticate and access the system's protected capabilities.

**Level:** User Goal

**Stakeholders and Interests:**

* **Unregistered User:** Needs a straightforward way to create an account to access prediction (user accounts).

* **Security Administrator:** Needs assurance that the chosen password enforces a minimum length of eight characters and maximum of twenty characters; is never stored in plaintext and is securely hashed using an appropriate cryptographic hash function before being saved.

**Preconditions:**

1. The system (frontend + backend + database) is online and accessible.

2. The user does not currently have an account with the required email

3. The user is not logged into the system.

**Main Success Scenario:**

1. The user accesses the registration section of the application.

2. The system prompts the user to provide a desired username, email and a password.

3. The user inputs a username, email and a password.

4. The system performs input validation to ensure the password meets the length requirements and to prevent trivial misuse.

5. The system verifies that the provided email is not already taken in the database.

6. The system securely hashes the password using an appropriate cryptographic hash function.

7. The system stores the new email, username, and the hashed password in the database.

8. The system logs the successful account creation, recording the timestamp and the new user's email and username.

9. The system informs the user of a successful registration and redirects them to the authentication/login flow.

**Extensions:**

4. a) Invalid input format or password too short/too big:

    * 4a1. The system catches the invalid input during validation.

    * 4a2. The system gracefully rejects the registration request, ensuring no internal implementation details are exposed.

    * 4a3. The system informs the user of the password and email requirements and prompts them to try again.

5. a) Email already exists:

    * 5a1. The system determines the requested email is already registered in the database.

    * 5a2. The system gracefully informs the user that the email is taken.

    * 5a3. The system prompts the user to choose a different email.