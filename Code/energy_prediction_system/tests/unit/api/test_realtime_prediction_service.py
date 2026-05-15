from unittest.mock import MagicMock, patch

import pandas as pd

from src.api.models.model import Model
from src.api.services.prediction_service import PredictionService


@patch("src.api.services.prediction_service.get_inference_engine")
@patch("src.api.services.prediction_service.pd.read_csv")
@patch("src.api.services.prediction_service.Path.exists")
def test_autoregressive_loop(mock_exists, mock_read_csv, mock_get_engine):
    """Verify that the autoregressive loop correctly updates L1_Load and other lags."""
    mock_exists.return_value = True

    # Mock data with 1 row (last valid context)
    data = {
        "datetime": ["2026-05-13T10:00:00Z"],
        "Load_MW": [100.0],
        "L1_Load": [99.0],
        "hour": [10],
        "day_of_week": [2],
        "month": [5],
        "year": [2026],
        "season": [2],
    }
    df = pd.DataFrame(data)
    mock_read_csv.return_value = df

    # Mock InferenceEngine
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    # First prediction returns 110.0, second returns 120.0
    mock_engine.predict.side_effect = [110.0, 120.0]

    # Mock Database session
    mock_db = MagicMock()
    mock_model = Model(
        model_pred_type="hourly",
        dataset_selected="full",
        top2_drivers="t2m, hour")
    mock_db.query().filter().first.return_value = mock_model

    result = PredictionService.get_realtime_prediction(
        mock_db, "hourly", historical_points=1, predicted_points=2)

    assert result["load_predicted"] == [110.0, 120.0]

    # Verify mock_engine.predict calls
    assert mock_engine.predict.call_count == 2

    # Check if the second call to predict had updated features
    # First call: uses features from last row (10:00)
    # Second call: uses features from first prediction (11:00)
    args, kwargs = mock_engine.predict.call_args_list[1]
    features_sent = args[1]
    assert features_sent["L1_Load"] == 110.0
    assert features_sent["hour"] == 11  # 10:00 + 1h = 11:00


@patch("src.api.services.inference_engine.joblib.load")
@patch("src.api.services.inference_engine.Path.exists")
def test_inference_engine_singleton_cache(mock_exists, mock_load):
    """Verify that models are loaded only once (Singleton pattern)."""
    from src.api.services.inference_engine import get_inference_engine

    mock_exists.return_value = True
    mock_load.return_value = MagicMock()  # Mocked model

    engine1 = get_inference_engine()
    engine2 = get_inference_engine()

    assert engine1 is engine2

    # Clear internal cache to ensure test isolation
    engine1._models.clear()

    # Load a model
    model_rec = MagicMock()
    model_rec.model_pred_type = "hourly"
    model_rec.model_server_relative_path = "models/test.joblib"
    model_rec.dataset_selected = "full"

    engine1.load_active_model(model_rec)
    engine1.load_active_model(model_rec)

    # Even if we call load_active_model multiple times, it just overwrites in
    # the dict
    assert len(engine1._models) == 1
