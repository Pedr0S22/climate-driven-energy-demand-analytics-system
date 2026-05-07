from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.database.session import get_db
from src.api.schemas.simulation import (
    TemplateInput,
    TemplateOutput,
    SimulationInput,
    SimulationOutput,
)
from src.api.services.simulation_service import SimulationService
router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("/templates", response_model=TemplateOutput)
def get_template(
    request: TemplateInput,
    db: Session = Depends(get_db)
):
    try:
        active_model = SimulationService.get_active_model(
            db, request.frequency)
        dataset_type = active_model.dataset_selected if active_model else "full"
        features = SimulationService.get_template(
            request.frequency, request.condition)

        return {
            "frequency": request.frequency,
            "condition": request.condition,
            "dataset_type": dataset_type,
            "features": features,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)) from e


@router.post("/run", response_model=SimulationOutput)
def run_simulation(request: SimulationInput, db: Session = Depends(get_db)):
    try:
        if request.overrides:
            errors = SimulationService.validate_overrides(request.overrides)
            if errors:
                raise ValueError(f"Erro de validação: {'; '.join(errors)}")

        result = SimulationService.run_simulation(
            db=db,
            frequency=request.frequency,
            template_name=request.template_name,
            month=request.month,
            day_of_week=request.day_of_week,
            overrides=request.overrides,
        )
        return SimulationOutput(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
