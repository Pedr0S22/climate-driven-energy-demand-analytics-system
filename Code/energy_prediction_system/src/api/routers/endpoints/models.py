from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.security import get_current_user, require_role
from src.api.database.session import get_db
from src.api.schemas.model import ModelSchema, ModelUpdate
from src.api.services.model_service import ModelService

router = APIRouter()


@router.get("/", response_model=list[ModelSchema])
def list_models(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return ModelService.get_all_models(db)


@router.patch("/{model_id}/activate", response_model=ModelSchema)
def activate_model(
    model_id: int,
    payload: ModelUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_role("admin")),
):
    if not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="is_active must be true to activate a model"
        )

    updated = ModelService.activate_model(db, model_id)
    return updated
