import re

# Validation Rules


def is_valid_email(email: str) -> bool:
    """Checks if email has at least one '@' and at least one '.'."""
    if not email:
        return False
    # regex for: text + @ + text + . + text
    regex = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(regex, email))


def has_min_max_length(text: str) -> bool:
    """Checks if text is between 8 and 20 characters."""
    return 8 <= len(text) <= 20


def has_uppercase(text: str) -> bool:
    """Checks for at least one uppercase letter."""
    return any(char.isupper() for char in text)


def has_number(text: str) -> bool:
    """Checks for at least one digit."""
    return any(char.isdigit() for char in text)


def has_special_char(text: str) -> bool:
    """Checks for at least one special character (non-alphanumeric)."""
    return any(not char.isalnum() for char in text)


# Form Validation Wrappers
def validate_login_input(email, password):
    """
    Validates Login form.
    """
    if not email.strip() or not password.strip():
        return False, "All fields are required."

    # Validate email format and password rules
    if not is_valid_email(email) or not all([has_min_max_length(password), has_uppercase(
            password), has_number(password), has_special_char(password)]):
        return False, "Invalid credentials."

    return True, None


def validate_registration_input(username, email, password, confirm_password):
    """
    Validates Registration form with specific feedback for each rule.
    """
    # Check for empty fields
    if not all([username.strip(),
                email.strip(),
                password.strip(),
                confirm_password.strip()]):
        return False, "All fields are required."

    # Email format
    if not is_valid_email(email):
        return False, "Invalid email format (e.g., user@domain.com)."

    # Password specific rules
    if not has_min_max_length(password):
        return False, "Password must be between 8 and 20 characters."

    if not has_uppercase(password):
        return False, "Password must contain at least one uppercase letter."

    if not has_number(password):
        return False, "Password must contain at least one number."

    if not has_special_char(password):
        return False, "Password must contain at least one special character."

    # Confirmation check
    if password != confirm_password:
        return False, "Passwords do not match."

    return True, None
