import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.core.security import get_current_user
from src.api.database.session import get_db
from src.api.schemas.prediction import PredictionResponse
from src.api.services.prediction_service import PredictionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/hourly", response_model=PredictionResponse)
def get_hourly_prediction(
    historical_points: int = Query(3, ge=3, le=5, description="Number of historical hours to include"),
    predicted_points: int = Query(12, ge=1, le=24, description="Number of hours to forecast"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get hourly electricity demand predictions.
    Default: 3h history, 12h forecast.
    Max: 5h history, 24h forecast.
    """
    try:
        result = PredictionService.get_realtime_prediction(
            db=db, frequency="hourly", historical_points=historical_points, predicted_points=predicted_points
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error in hourly prediction endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during prediction") from e


@router.get("/daily", response_model=PredictionResponse)
def get_daily_prediction(
    historical_points: int = Query(3, ge=1, le=5, description="Number of historical days to include"),
    predicted_points: int = Query(7, ge=1, le=14, description="Number of days to forecast"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get daily electricity demand predictions.
    Default: 3d history, 7d forecast.
    Max: 5d history, 14d forecast.
    """
    try:
        result = PredictionService.get_realtime_prediction(
            db=db, frequency="daily", historical_points=historical_points, predicted_points=predicted_points
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e1:
        logger.error(f"Error in daily prediction endpoint: {e1}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error during prediction") from e1
