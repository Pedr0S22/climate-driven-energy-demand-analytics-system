from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.api.models.model import Model
from src.api.services.inference_engine import get_inference_engine


class ModelService:
    @staticmethod
    def get_all_models(db: Session) -> list[Model]:
        """Retrieve all models ordered by creation date (newest first)"""
        return db.query(Model).order_by(Model.model_creation_date.desc()).all()

    @staticmethod
    def get_model_by_id(db: Session, model_id: int) -> Model | None:
        """Get specific model by ID"""
        model = db.query(Model).filter(Model.model_name_id == model_id).first()
        if not model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model with id {model_id} not found")
        return model

    @staticmethod
    def activate_model(db: Session, model_id: int) -> Model | None:
        model_to_activate = ModelService.get_model_by_id(db, model_id)

        # Verificar se já está ativo
        if model_to_activate.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Model {model_id} is already active")

        try:
            # Mutex: Desativar todos os outros modelos do mesmo tipo
            db.query(Model).filter(
                and_(Model.model_pred_type == model_to_activate.model_pred_type, Model.is_active)
            ).update({"is_active": False})

            model_to_activate.is_active = True
            db.commit()
            db.refresh(model_to_activate)

            engine = get_inference_engine()
            engine.load_active_model(model_to_activate)

            return model_to_activate

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error activating model: {str(e)}"
            ) from e
