from pydantic import BaseModel, Field


class DailySimulationInput(BaseModel):
    template_name: str = Field(..., description="Weather condition: 'average', 'rainy', 'storm', 'heatwave'")
    year: int = Field(..., ge=2020, le=2026, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    overrides: dict[str, float] | None = Field(default=None, description="Feature overrides")


class HourlySimulationInput(DailySimulationInput):
    hour: int = Field(..., ge=0, le=23, description="Hour (0-23)")


class SimulationOutput(BaseModel):
    """Output da simulação"""

    predicted_mw: float = Field(..., description="Predicted load in MW")
    top_drivers: list[str] = Field(..., description="Top 2 features that most influenced the prediction")


class TemplateInput(BaseModel):
    """Input para pedir um template"""

    frequency: str = Field(..., description="Prediction frequency: 'daily' or 'hourly'")
    template_name: str = Field(..., description="Weather condition: 'average', 'rainy', 'storm', 'heatwave'")


class TemplateOutput(BaseModel):
    """Output com o template de features"""

    frequency: str
    template_name: str
    dataset_type: str
    features: dict[str, float] = Field(..., description="Feature vector with default values (Celsius, hPa, m/s, etc.)")
