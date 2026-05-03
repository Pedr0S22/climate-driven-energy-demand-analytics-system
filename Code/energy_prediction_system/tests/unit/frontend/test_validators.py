from src.app.utils.validators import (
    has_min_max_length,
    has_number,
    has_special_char,
    has_uppercase,
    is_valid_email,
    validate_login_input,
    validate_registration_input,
)


class TestValidators:
    """Unit tests for pure validation rules."""

    # Atomic Rules Tests 

    def test_is_valid_email(self):
        assert is_valid_email("test@example.com") is True
        assert is_valid_email("user@domain.co.uk") is True
        assert is_valid_email("invalid-email") is False
        assert is_valid_email("user@no-dot") is False
        assert is_valid_email("") is False

    def test_has_min_max_length(self):
        assert has_min_max_length("1234567") is False  # 7 chars
        assert has_min_max_length("12345678") is True  # 8 chars
        assert has_min_max_length("a" * 20) is True    # 20 chars
        assert has_min_max_length("a" * 21) is False   # 21 chars

    def test_has_uppercase(self):
        assert has_uppercase("lowercase") is False
        assert has_uppercase("Uppercase") is True
        assert has_uppercase("123!@#") is False

    def test_has_number(self):
        assert has_number("no-numbers") is False
        assert has_number("number1") is True

    def test_has_special_char(self):
        assert has_special_char("NoSpecialChar123") is False
        assert has_special_char("Special!Char") is True
        assert has_special_char("Password@123") is True

    # Login Validation Tests 

    def test_validate_login_input_success(self):
        success, message = validate_login_input("valid@email.com", "Secure@123")
        assert success is True
        assert message is None

    def test_validate_login_input_empty(self):
        success, message = validate_login_input(" ", "password")
        assert success is False
        assert message == "All fields are required."

    def test_validate_login_invalid_format(self):
        """Ensures login returns generic error for security when format is wrong."""
        # Invalid email format
        success, message = validate_login_input("invalidemail", "Secure@123")
        assert success is False
        assert message == "Invalid credentials."
        
        # Weak password format
        success, message = validate_login_input("valid@email.com", "123")
        assert success is False
        assert message == "Invalid credentials."

    # Registration Validation Tests

    def test_validate_registration_success(self):
        success, message = validate_registration_input(
            "username", "test@test.com", "Strong@123", "Strong@123"
        )
        assert success is True
        assert message is None

    def test_validate_registration_empty_fields(self):
        success, message = validate_registration_input("", "test@test.com", "Pass", "")
        assert success is False
        assert message == "All fields are required."

    def test_validate_registration_email_error(self):
        success, message = validate_registration_input(
            "user", "wrong-email", "Strong@123", "Strong@123"
        )
        assert success is False
        assert "Invalid email format" in message

    def test_validate_registration_password_specific_errors(self):
        # Test length
        s, m = validate_registration_input("u", "t@t.com", "Short1!", "Short1!")
        assert s is False
        assert "between 8 and 20 characters" in m

        # Test uppercase
        s, m = validate_registration_input("u", "t@t.com", "lowercase1!", "lowercase1!")
        assert s is False
        assert "uppercase letter" in m

        # Test number
        s, m = validate_registration_input("u", "t@t.com", "NoNumbers!", "NoNumbers!")
        assert s is False
        assert "at least one number" in m

        # Test special char
        s, m = validate_registration_input("u", "t@t.com", "NoSpecial1", "NoSpecial1")
        assert s is False
        assert "special character" in m

    def test_validate_registration_password_mismatch(self):
        success, message = validate_registration_input(
            "user", "test@test.com", "Strong@123", "Different@123"
        )
        assert success is False
        assert message == "Passwords do not match."