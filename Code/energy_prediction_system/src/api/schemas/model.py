from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ModelBase(BaseModel):
    model_type: str = Field(...,
                            description="Model type: 'Random Forest', 'Linear Regression', etc.")
    model_pred_type: str = Field(...,
                                 description="Prediction frequency: 'daily' or 'hourly'")
    model_server_relative_path: str = Field(...,
                                            description="Path to model file on server")
    dataset_selected: str = Field(...,
                                  description="Dataset type: 'full', 'selected', or 'pca'")
    top2_drivers: str = Field(...,
                              description="Top 2 feature drivers (comma-separated)")
    rmse: float | None = Field(None, description="Root Mean Square Error")
    r2: float | None = Field(None, description="R² score")
    mae: float | None = Field(None, description="Mean Absolute Error")


class ModelUpdate(BaseModel):
    is_active: bool = Field(...,
                            description="Set to true to activate this model")


class ModelSchema(ModelBase):
    model_name_id: int
    model_creation_date: datetime
    is_active: bool = False

    # Permite ler objetos do SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
