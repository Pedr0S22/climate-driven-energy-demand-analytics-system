import os
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from src.api.database.session import Base
from src.api.models.model import Model
from src.api.services.inference_engine import InferenceEngine, get_inference_engine
from src.api.services.prediction_service import PredictionService
from src.api.services.simulation_service import SimulationService

# --- DB SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_services.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("./test_api_services.db"):
            try:
                os.remove("./test_api_services.db")
            except:  # noqa E722 S110
                pass


def _next_id(db):
    max_id = db.query(func.max(Model.model_name_id)).scalar() or 0
    return max_id + 1


@pytest.fixture
def mock_ml_assets():
    """Mocks joblib.load to return dummy models/scalers/pca"""
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([50000.0])
    # Mocking as numpy array because the code calls .tolist()
    mock_model.feature_names_in_ = np.array(["L1_Load", "t2m"])

    mock_scaler = MagicMock()
    mock_scaler.transform.side_effect = lambda x: x
    mock_scaler.feature_names_in_ = np.array(["L1_Load", "t2m"])

    mock_pca = MagicMock()
    # PCA transform returns a numpy array
    mock_pca.transform.side_effect = lambda x: np.array([[1.0, 0.5]])

    with (
        patch("src.api.services.inference_engine.joblib.load") as mock_load,
        patch("src.api.services.inference_engine.Path.exists", return_value=True),
    ):

        def side_effect(path):
            p = str(path)
            if "scaler" in p:
                return mock_scaler
            if "pca" in p:
                return mock_pca
            return mock_model

        mock_load.side_effect = side_effect
        yield {"model": mock_model, "scaler": mock_scaler, "pca": mock_pca}


def test_inference_engine_lifecycle(db_session, mock_ml_assets):
    """Test loading and predicting with InferenceEngine"""
    ie = InferenceEngine()
    # Reset state to ensure clean test
    ie._models = {}
    ie._scalers = {}
    ie._pca = {}

    # Create a dummy model record
    m_record = Model(
        model_name_id=_next_id(db_session),
        model_type="RandomForest",
        model_pred_type="daily",
        dataset_selected="pca",
        is_active=True,
        model_server_relative_path="models/daily/test.joblib",
        top2_drivers="t2m, L1_Load",
        rmse=0.1,
        mae=0.1,
        r2=0.9,
    )
    db_session.add(m_record)
    db_session.commit()

    # Load
    success = ie.load_active_model(m_record)
    assert success is True
    assert "daily" in ie._models
    assert "daily" in ie._scalers
    assert "daily" in ie._pca

    # Predict
    features = {"L1_Load": 600000.0, "t2m": 25.0}
    pred = ie.predict("daily", features)
    assert pred == 50000.0


def test_prediction_service_autoregressive(db_session, mock_ml_assets):
    """Test PredictionService with mocked CSV data"""
    # 1. Setup active model
    m_record = Model(
        model_name_id=_next_id(db_session),
        model_type="RandomForest",
        model_pred_type="daily",
        dataset_selected="full",
        is_active=True,
        model_server_relative_path="models/daily/RF.joblib",
        top2_drivers="t2m, L1_Load",
        rmse=0.1,
        mae=0.1,
        r2=0.9,
    )
    db_session.add(m_record)
    db_session.commit()

    # 2. Mock CSV data
    dummy_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
            "Load_MWh": [590000.0, 600000.0, 610000.0],
            "t2m": [9.0, 10.0, 11.0],
            "L1_Load": [580000.0, 590000.0, 600000.0],
        }
    )

    # Ensure InferenceEngine has the model
    ie = get_inference_engine()
    ie.load_active_model(m_record)

    with (
        patch("src.api.services.prediction_service.pd.read_csv", return_value=dummy_data),
        patch("src.api.services.prediction_service.Path.exists", return_value=True),
    ):
        result = PredictionService.get_realtime_prediction(db_session, "daily", 2, 3)

        assert result["status"] == 200
        assert len(result["load_predicted"]) == 3
        assert len(result["historical_load"]) == 2
        assert result["top2_drivers"] == ["t2m", "L1_Load"]


def test_simulation_service_scenarios(db_session, mock_ml_assets):
    """Test SimulationService scenarios and overrides"""
    m_record = Model(
        model_name_id=_next_id(db_session),
        model_type="LinearRegression",
        model_pred_type="hourly",
        dataset_selected="full",
        is_active=True,
        model_server_relative_path="models/hourly/LR.joblib",
        top2_drivers="t2m, hour",
        rmse=0.1,
        mae=0.1,
        r2=0.9,
    )
    db_session.add(m_record)
    db_session.commit()

    # Ensure InferenceEngine has the model
    ie = get_inference_engine()
    ie.load_active_model(m_record)

    # 1. Run standard simulation
    sim_result = SimulationService.run_simulation(db_session, "hourly", "average", 2024, 5, 2, hour=12)
    assert "predicted_mw" in sim_result
    assert sim_result["predicted_mw"] == 50000.0

    # 2. Run with valid overrides
    sim_result_ov = SimulationService.run_simulation(
        db_session, "hourly", "heatwave", 2024, 7, 3, hour=15, overrides={"t2m": 45.0, "tp": 0.0}
    )
    assert sim_result_ov["predicted_mw"] == 50000.0

    # 3. Test invalid overrides (Restriction)
    with pytest.raises(ValueError, match="Override não permitido"):
        SimulationService.run_simulation(
            db_session,
            "hourly",
            "average",
            2024,
            5,
            2,
            12,
            overrides={"skt": 30.0},  # Not in ALLOWED_OVERRIDES
        )

    # 4. Test physical limits
    with pytest.raises(ValueError, match="deve estar entre"):
        SimulationService.run_simulation(
            db_session,
            "hourly",
            "average",
            2024,
            5,
            2,
            12,
            overrides={"t2m": 100.0},  # Outside physical limit
        )


def test_inference_engine_missing_model(db_session):
    """Test error handling when model is missing"""
    ie = InferenceEngine()
    ie._models = {}  # Clear models

    with pytest.raises(ValueError, match="Nenhum modelo ativo carregado"):
        ie.predict("daily", {"any": 1})


def test_prediction_service_no_active_model(db_session):
    """Test error handling when no model is active in DB"""
    with pytest.raises(ValueError, match="Nenhum modelo ativo encontrado"):
        PredictionService.get_realtime_prediction(db_session, "daily", 1, 1)
