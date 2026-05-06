from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


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
    rmse: Optional[float] = Field(None, description="Root Mean Square Error")
    r2: Optional[float] = Field(None, description="R² score")
    mae: Optional[float] = Field(None, description="Mean Absolute Error")


class ModelUpdate(BaseModel):
    is_active: bool = Field(...,
                            description="Set to true to activate this model")


class ModelSchema(ModelBase):
    model_name_id: int
    model_creation_date: datetime
    is_active: bool = False

    class Config:
        from_attributes = True  # Permite ler objetos do SQLAlchemy
