import logging
from pathlib import Path

import joblib
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_realtime_prediction(freq="daily", ds_type="selected", model_prefix="LR"):
    """
    Tests if a model can make predictions on real-time engineered data.
    """
    APP_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = APP_ROOT / "data" / "processed" / "feat-engineering" / "real-time"
    MODELS_DIR = APP_ROOT / "models" / freq

    # 1. Load Real-time Engineered Data
    data_path = DATA_DIR / f"realtime_{freq}_{ds_type}.csv"
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {freq} {ds_type} data with shape: {df.shape}")

    # 2. Load Model
    model_files = sorted(MODELS_DIR.glob(f"{model_prefix}_v*.joblib"), reverse=True)
    if not model_files:
        logger.error(f"No model found for {model_prefix} in {MODELS_DIR}")
        return

    model_path = model_files[0]
    model = joblib.load(model_path)
    logger.info(f"Loaded model: {model_path}")

    # 3. Prepare features
    if hasattr(model, "feature_names_in_"):
        expected_features = model.feature_names_in_.tolist()
        logger.info(f"Model expects {len(expected_features)} features.")

        # Check for differences
        actual_features = df.columns.tolist()
        missing = [f for f in expected_features if f not in actual_features]
        extra = [
            f for f in actual_features if f not in expected_features and f not in ["datetime", "Load_MWh", "Load_MW"]
        ]

        if missing:
            logger.warning(f"MISSING features in data: {missing}")
        if extra:
            logger.info(f"EXTRA features in data (will be ignored): {extra[:5]}...")

        # Reorder to match model
        try:
            X = df[expected_features].fillna(0)
            logger.info("Successfully reordered data columns to match model expectations.")
        except KeyError as e:
            logger.error(f"Cannot reorder columns: {e}")
            return
    else:
        # Fallback for models without feature names (shouldn't happen with scikit-learn >= 1.0)
        target_col = "Load_MWh" if freq == "daily" else "Load_MW"
        X = df.drop(columns=[c for c in ["datetime", target_col] if c in df.columns]).fillna(0)

    # 4. Predict
    try:
        preds = model.predict(X)
        logger.info(f"Successfully predicted {len(preds)} values.")
        logger.info(f"Sample predictions: {preds[:5]}")
        print(f"\nPrediction test for {freq} {ds_type} using {model_prefix} SUCCESSFUL!")

        # Check if columns were already in order
        if hasattr(model, "feature_names_in_"):
            data_cols = [c for c in df.columns if c in expected_features]
            if data_cols == expected_features:
                print("COLUMNS WERE ALREADY IN THE CORRECT ORDER!")
            else:
                print("COLUMNS HAD TO BE REORDERED.")

    except Exception as e:
        logger.error(f"Prediction failed: {e}")


if __name__ == "__main__":
    # Test Daily Selected with LR (Linear Regression)
    for model_prefix in ["LR", "RF"]:
        for fr in ["daily", "hourly"]:
            for ds_type in ["full", "selected", "pca"]:
                logger.info(f"Testing {fr} {ds_type} Prediction with {model_prefix}...")
                test_realtime_prediction(freq=fr, ds_type=ds_type, model_prefix=model_prefix)
