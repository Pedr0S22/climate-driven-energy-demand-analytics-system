import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox

# Ensure PYTHONPATH includes src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.core.security import get_current_user
from src.api.database.session import Base, get_db
from src.api.main import app
from src.app.manager.session_manager import SessionManager
from src.app.ui.main_window import MainWindow

# --- SETUP TEST DATABASE ---
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user(db: Session = pytest.importorskip("fastapi").Depends(override_get_db)):
    from src.api.models.user import Admin, User

    try:
        user = db.query(User).filter(User.email == "admin@test.com").first()
        if not user:
            from src.api.core.security import get_password_hash

            user = User(username="admin_test", email="admin@test.com", password=get_password_hash("AdminPass123!"))
            db.add(user)
            db.commit()
            db.refresh(user)

            # Ensure it has admin role
            admin_role = Admin(users_id=user.id)
            db.add(admin_role)
            db.commit()
        return user
    except Exception:
        # Tables might be gone during teardown
        return None


# --- MOCK KEYRING ---
fake_keyring = {}


def mock_set_password(service, username, password):
    fake_keyring[(service, username)] = password


def mock_get_password(service, username):
    return fake_keyring.get((service, username))


def mock_delete_password(service, username):
    if (service, username) in fake_keyring:
        del fake_keyring[(service, username)]


@pytest.fixture(autouse=True)
def setup_db():
    # Apply dependency overrides
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    Base.metadata.create_all(bind=engine)
    fake_keyring.clear()
    SessionManager.clear_session()

    with (
        patch("src.app.manager.session_manager.keyring.set_password", side_effect=mock_set_password),
        patch("src.app.manager.session_manager.keyring.get_password", side_effect=mock_get_password),
        patch("src.app.manager.session_manager.keyring.delete_password", side_effect=mock_delete_password),
    ):
        yield

    Base.metadata.drop_all(bind=engine)

    # Remove dependency overrides
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

    if os.path.exists("./test_ui_integration.db"):
        try:
            os.remove("./test_ui_integration.db")
        except:  # noqa E722 S110
            pass


@pytest.fixture
def api_client():
    return TestClient(app)


@pytest.fixture
def main_window(qtbot, api_client):
    """
    Creates the MainWindow and patches requests to use TestClient.
    """

    def mock_request_adapter(method):
        def wrapper(url, **kwargs):
            endpoint = url.replace("http://localhost", "")
            kwargs.pop("timeout", None)
            client_method = getattr(api_client, method)
            return client_method(endpoint, **kwargs)

        return wrapper

    with (
        patch("src.app.client.api_client.requests.get", side_effect=mock_request_adapter("get")),
        patch("src.app.client.api_client.requests.post", side_effect=mock_request_adapter("post")),
        patch("src.app.client.api_client.requests.patch", side_effect=mock_request_adapter("patch")),
        patch("src.app.client.api_client.requests.put", side_effect=mock_request_adapter("put")),
        patch("src.app.client.api_client.requests.delete", side_effect=mock_request_adapter("delete")),
    ):
        window = MainWindow()
        qtbot.addWidget(window)
        yield window

        # Cleanup: wait for any background threads to finish
        def wait_for_workers():
            try:
                workers = ["login_worker", "profile_worker", "register_worker", "logout_worker", "prediction_worker"]
                for attr in workers:
                    worker = getattr(window, attr, None)
                    if worker and worker.isRunning():
                        return False
                # Also check workers in views
                if hasattr(window, "ui_model_mgmt") and hasattr(window.ui_model_mgmt, "load_worker"):
                    if window.ui_model_mgmt.load_worker.isRunning():
                        return False
                return True
            except RuntimeError:
                # Window might have been deleted already
                return True

        qtbot.waitUntil(wait_for_workers, timeout=5000)
        try:
            window.close()
        except RuntimeError:
            pass


# --- TESTS ---


def test_ui_login_success_admin(main_window, qtbot):
    """
    Tests the full login flow from UI to Backend for an Admin user.
    """
    from src.api.core.security import get_password_hash
    from src.api.models.user import Admin, User

    db = TestingSessionLocal()
    if not db.query(User).filter(User.email == "admin@test.com").first():
        admin_user = User(username="admin_test", email="admin@test.com", password=get_password_hash("AdminPass123!"))
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        admin_role = Admin(users_id=admin_user.id)
        db.add(admin_role)
        db.commit()
    db.close()

    main_window.ui_login.email_input.setText("admin@test.com")
    main_window.ui_login.pass_input.setText("AdminPass123!")
    qtbot.mouseClick(main_window.ui_login.login_button, QtCore.Qt.MouseButton.LeftButton)

    # Wait for page transition AND for the profile worker to finish updating the label
    qtbot.waitUntil(lambda: main_window.stack.currentIndex() == 2, timeout=10000)
    qtbot.waitUntil(lambda: "admin_test" in main_window.ui_admin.top_bar.title_label.text(), timeout=5000)

    assert main_window.stack.currentIndex() == 2
    assert SessionManager.get_role() == "admin"


def test_ui_login_failure(main_window, qtbot):
    """
    Tests the login failure message box.
    """
    main_window.ui_login.email_input.setText("wrong@test.com")
    main_window.ui_login.pass_input.setText("wrongpass")

    with patch.object(QMessageBox, "warning") as mock_warning:
        qtbot.mouseClick(main_window.ui_login.login_button, QtCore.Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: mock_warning.called, timeout=5000)

    assert main_window.stack.currentIndex() == 0


def test_ui_registration_flow(main_window, qtbot):
    """
    Tests the registration flow from UI to Backend.
    """
    qtbot.mouseClick(main_window.ui_login.register_link, QtCore.Qt.MouseButton.LeftButton)
    assert main_window.stack.currentIndex() == 1

    main_window.ui_register.user_input.setText("new_user")
    main_window.ui_register.email_input.setText("new@test.com")
    main_window.ui_register.pass_input.setText("Pass123!@#")
    main_window.ui_register.conf_pass_input.setText("Pass123!@#")

    with patch.object(QMessageBox, "information") as mock_info:  # noqa F841
        qtbot.mouseClick(main_window.ui_register.signup_button, QtCore.Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: main_window.stack.currentIndex() == 0, timeout=10000)

    assert main_window.stack.currentIndex() == 0

    db = TestingSessionLocal()
    from src.api.models.user import User

    user = db.query(User).filter(User.email == "new@test.com").first()
    assert user is not None
    assert user.username == "new_user"
    db.close()


def test_ui_navigation_sidebar(main_window, qtbot):
    """
    Tests navigation through the sidebar after login.
    """
    SessionManager.set_session("fake-token", "admin")
    main_window.stack.setCurrentIndex(2)

    qtbot.mouseClick(main_window.ui_admin.toolButton, QtCore.Qt.MouseButton.LeftButton)
    assert main_window.ui_admin.sidebar.isVisible()

    qtbot.mouseClick(main_window.ui_admin.daily_btn, QtCore.Qt.MouseButton.LeftButton)
    assert main_window.stack.currentIndex() == 3

    with patch.object(QMessageBox, "warning"), patch.object(QMessageBox, "exec"):
        qtbot.mouseClick(main_window.ui_daily_pred.model_btn, QtCore.Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: main_window.stack.currentIndex() == 5, timeout=5000)

    assert main_window.stack.currentIndex() == 5
