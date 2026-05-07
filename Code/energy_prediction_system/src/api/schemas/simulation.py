from pydantic import BaseModel, Field
from typing import Optional, Dict, List


class SimulationInput(BaseModel):
    frequency: str = Field(...,
                           description="Prediction frequency: 'daily' or 'hourly'")
    template_name: str = Field(
        ..., description="Weather condition: 'average', 'rainy', 'storm', 'heatwave'")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day_of_week: int = Field(..., ge=0, le=6,
                             description="Day of week (0=Monday, 6=Sunday)")
    overrides: Optional[Dict[str, float]] = Field(
        default=None, description="Feature overrides")


class SimulationOutput(BaseModel):
    """Output da simulação"""
    predicted_mw: float = Field(..., description="Predicted load in MW")
    top_drivers: List[str] = Field(
        ...,
        description="Top 2 features that most influenced the prediction"
    )


class TemplateInput(BaseModel):
    """Input para pedir um template"""
    frequency: str = Field(
        ...,
        description="Prediction frequency: 'daily' or 'hourly'"
    )
    condition: str = Field(...,
                           description="Weather condition: 'average', 'rainy', 'storm', 'heatwave'")


class TemplateOutput(BaseModel):
    """Output com o template de features"""
    frequency: str
    condition: str
    dataset_type: str
    features: Dict[str, float] = Field(
        ...,
        description="Feature vector with default values (Celsius, hPa, m/s, etc.)"
    )
