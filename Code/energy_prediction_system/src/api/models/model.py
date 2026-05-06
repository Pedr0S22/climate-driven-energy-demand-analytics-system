from sqlalchemy import Column, BigInteger, String, Boolean, Float, DateTime, Index
from sqlalchemy.sql import func
from src.api.database.session import Base


class Model(Base):
    __tablename__ = "model"

    # Usando BigInteger para corresponder ao BIGSERIAL do banco
    model_name_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Campos obrigatórios do banco
    model_type = Column(String(512), nullable=False)
    model_creation_date = Column(DateTime(timezone=True),
                                 server_default=func.current_timestamp(),
                                 nullable=False)
    model_pred_type = Column(String(512),
                             nullable=False)  # 'daily' ou 'hourly'
    model_server_relative_path = Column(String(512), nullable=False)
    # 'full', 'selected', 'pca'
    dataset_selected = Column(String(512), nullable=False)
    top2_drivers = Column(String(512), nullable=False)

    # Métricas estatísticas
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)

    # Status
    is_active = Column(Boolean, nullable=False, default=False)

    # Índice único para garantir apenas um modelo ativo por tipo
    __table_args__ = (
        Index('one_active_model_per_type',
              'model_pred_type',
              unique=True,
              postgresql_where=(is_active)),
    )
