from datetime import datetime

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """DTO for prediction results including historical and forecast data."""

    status: int = Field(200, description="HTTP Status Code")
    historical_load: list[float] = Field(..., description="Array of historical load values")
    load_predicted: list[float] = Field(..., description="Array of predicted load values")
    timestamps: list[datetime] = Field(
        ..., description="Unified array of UTC timestamps for historical and predicted points"
    )
    top2_drivers: list[str] = Field(..., description="Top 2 variables driving the prediction")

    class Config:
        json_schema_extra = {
            "example": {
                "status": 200,
                "historical_load": [25000.5, 26100.2, 25800.8],
                "load_predicted": [26000.0, 26500.5, 27000.2],
                "timestamps": [
                    "2026-05-12T10:00:00Z",
                    "2026-05-12T11:00:00Z",
                    "2026-05-12T12:00:00Z",
                    "2026-05-12T13:00:00Z",
                    "2026-05-12T14:00:00Z",
                    "2026-05-12T15:00:00Z",
                ],
                "top2_drivers": ["t2m", "L1_Load"],
            }
        }
