from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.security import get_current_user
from src.api.database.session import get_db
from src.api.schemas.simulation import (
    DailySimulationInput,
    HourlySimulationInput,
    SimulationOutput,
    TemplateInput,
    TemplateOutput,
)
from src.api.services.simulation_service import SimulationService

router = APIRouter()


@router.post("/templates", response_model=TemplateOutput)
def get_template(
        request: TemplateInput,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)):
    try:
        # Tenta descobrir o dataset_type pelo modelo ativo
        active_model = SimulationService.get_active_model(
            db, request.frequency)
        dataset_type = active_model.dataset_selected if active_model else "full"
        # Se for PCA, o template base deve ser 'full'
        if dataset_type == "pca":
            dataset_type = "full"

        features = SimulationService.get_template(
            request.frequency, request.template_name, dataset_type)

        return {
            "frequency": request.frequency,
            "template_name": request.template_name,
            "dataset_type": dataset_type,
            "features": features,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)) from e


@router.post("/daily", response_model=SimulationOutput)
def run_daily_simulation(
        request: DailySimulationInput,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)):
    try:
        result = SimulationService.run_simulation(
            db=db,
            frequency="daily",
            template_name=request.template_name,
            year=request.year,
            month=request.month,
            day_of_week=request.day_of_week,
            overrides=request.overrides,
        )
        return SimulationOutput(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/hourly", response_model=SimulationOutput)
def run_hourly_simulation(
        request: HourlySimulationInput,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)):
    try:
        result = SimulationService.run_simulation(
            db=db,
            frequency="hourly",
            template_name=request.template_name,
            year=request.year,
            month=request.month,
            day_of_week=request.day_of_week,
            hour=request.hour,
            overrides=request.overrides,
        )
        return SimulationOutput(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
