import logging
from typing import Any

from sqlalchemy.orm import Session

from src.api.models.model import Model
from src.api.services.inference_engine import get_inference_engine

logger = logging.getLogger(__name__)

# ============================================================
# LIMITES FÍSICOS PARA VALIDAÇÃO
# ============================================================
# u10 and v10 are vector components and can be negative.
PHYSICAL_LIMITS = {
    "t2m": (-40.0, 55.0),  # Celsius - temperatura a 2m
    "skt": (-40.0, 55.0),  # Celsius - temperatura da pele
    "d2m": (-40.0, 55.0),  # Celsius - temperatura do ponto de orvalho
    "stl1": (-40.0, 65.0),  # Celsius - temperatura do solo nível 1
    # m/s - componente U do vento (pode ser negativo)
    "u10": (-69.4, 69.4),
    # m/s - componente V do vento (pode ser negativo)
    "v10": (-69.4, 69.4),
    # mm - precipitação total (não pode ser negativa)
    "tp": (0.0, 55.0),
    # J/m² - radiação solar (não pode ser negativa)
    "ssrd": (0.0, float("inf")),
}

# Variáveis validadas apenas por IQR (não têm limites físicos fixos):
# strd, sp, swvl1

# ============================================================
# TEMPLATE STORE: 16 cenários base
# (4 conditions) x (2 dataset types: Full, Selected) x (2 frequencies: Daily, Hourly) = 16
# ============================================================
TEMPLATES: dict[str, dict[str, float]] = {}

BASE_TEMPLATES = {
    # ============ DAILY ============
    "daily_average": {
        "t2m": 20.0,
        "skt": 22.0,
        "tp": 0.0,
        "ssrd": 2000000.0,
        "sp": 101325.0,
        "u10": 3.0,
        "v10": 2.0,
        "d2m": 10.0,
        "stl1": 21.0,
        "strd": 1500000.0,
        "swvl1": 0.35,
    },
    "daily_rainy": {
        "t2m": 15.0,
        "skt": 16.0,
        "tp": 25.0,
        "ssrd": 500000.0,
        "sp": 100500.0,
        "u10": 8.0,
        "v10": 6.0,
        "d2m": 14.0,
        "stl1": 15.0,
        "strd": 1200000.0,
        "swvl1": 0.65,
    },
    "daily_storm": {
        "t2m": 10.0,
        "skt": 11.0,
        "tp": 45.0,
        "ssrd": 200000.0,
        "sp": 98000.0,
        "u10": -30.0,
        "v10": -25.0,
        "d2m": 9.0,
        "stl1": 10.0,
        "strd": 800000.0,
        "swvl1": 0.85,
    },
    "daily_heatwave": {
        "t2m": 42.0,
        "skt": 48.0,
        "tp": 0.0,
        "ssrd": 3500000.0,
        "sp": 102000.0,
        "u10": 2.0,
        "v10": 1.0,
        "d2m": 18.0,
        "stl1": 45.0,
        "strd": 2500000.0,
        "swvl1": 0.10,
    },
    # ============ HOURLY ============
    "hourly_average": {
        "t2m": 18.0,
        "skt": 20.0,
        "tp": 0.0,
        "ssrd": 250.0,
        "sp": 101325.0,
        "u10": 3.0,
        "v10": 2.0,
        "d2m": 9.0,
        "stl1": 19.0,
        "strd": 200.0,
        "swvl1": 0.35,
    },
    "hourly_rainy": {
        "t2m": 13.0,
        "skt": 14.0,
        "tp": 5.0,
        "ssrd": 50.0,
        "sp": 100500.0,
        "u10": 8.0,
        "v10": 6.0,
        "d2m": 12.0,
        "stl1": 13.0,
        "strd": 100.0,
        "swvl1": 0.65,
    },
    "hourly_storm": {
        "t2m": 9.0,
        "skt": 10.0,
        "tp": 12.0,
        "ssrd": 20.0,
        "sp": 98000.0,
        "u10": -35.0,
        "v10": -30.0,
        "d2m": 8.0,
        "stl1": 9.0,
        "strd": 50.0,
        "swvl1": 0.85,
    },
    "hourly_heatwave": {
        "t2m": 45.0,
        "skt": 50.0,
        "tp": 0.0,
        "ssrd": 400.0,
        "sp": 102000.0,
        "u10": 2.0,
        "v10": 1.0,
        "d2m": 20.0,
        "stl1": 47.0,
        "strd": 350.0,
        "swvl1": 0.10,
    },
}


for key, values in BASE_TEMPLATES.items():
    # Full dataset: todas as features
    TEMPLATES[f"{key}_full"] = values.copy()

for key, values in BASE_TEMPLATES.items():
    # Selected dataset: subset (sem strd, sp, swvl1)
    selected = {k: v for k, v in values.items() if k not in ["strd", "sp", "swvl1"]}
    TEMPLATES[f"{key}_selected"] = selected


class SimulationService:
    """Serviço de simulação com 16 templates e lógica de overrides"""

    @staticmethod
    def get_active_model(db: Session, frequency: str) -> Model | None:
        """Obtém o modelo ativo para uma frequência (normalizada)"""
        normalized_freq = frequency.strip().lower()
        model = db.query(Model).filter(Model.model_pred_type == normalized_freq, Model.is_active).first()

        if not model:
            logger.warning(f"Nenhum modelo ativo encontrado para frequência: '{normalized_freq}'")
            # Fallback: tentar buscar sem normalizar se falhou
            model = db.query(Model).filter(Model.model_pred_type == frequency, Model.is_active).first()

        return model

    @staticmethod
    def get_template(frequency: str, condition: str, dataset_type: str = "full") -> dict[str, Any]:
        """
        Obtém o template para uma condição climática.

        Args:
            frequency: 'daily' ou 'hourly'
            condition: 'average', 'rainy', 'storm', 'heatwave'
            dataset_type: 'full' ou 'selected'

        Returns:
            Dicionário com os valores base do template
        """
        template_key = f"{frequency}_{condition}_{dataset_type}"
        if template_key not in TEMPLATES:
            raise ValueError(
                f"Template '{template_key}' não encontrado. " f"Opções disponíveis: {sorted(TEMPLATES.keys())}"
            )
        return TEMPLATES[template_key].copy()

    @staticmethod
    def validate_overrides(overrides: dict[str, float]) -> list[str]:
        """
        Valida os overrides contra limites físicos.
        Variáveis strd, sp, swvl1 não têm limites fixos (apenas IQR).

        Args:
            overrides: Dicionário com features e valores a validar

        Returns:
            Lista de erros de validação (vazia se tudo OK)
        """
        errors = []
        units = {
            "t2m": "°C",
            "skt": "°C",
            "d2m": "°C",
            "stl1": "°C",
            "u10": "m/s",
            "v10": "m/s",
            "tp": "mm",
            "ssrd": "J/m²",
        }
        for feature, value in overrides.items():
            if feature in PHYSICAL_LIMITS:
                min_val, max_val = PHYSICAL_LIMITS[feature]
                if value < min_val or value > max_val:
                    unit = units.get(feature, "")
                    errors.append(f"'{feature}' deve estar entre {min_val} e {max_val} {unit}, " f"recebeu {value}")
        return errors

    @staticmethod
    def apply_overrides(base_features: dict[str, float], overrides: dict[str, float]) -> dict[str, float]:
        """
        Aplica overrides ao template base.
        Substitui os valores base pelos valores do utilizador.
        """
        features = base_features.copy()
        if overrides:
            features.update(overrides)
        return features

    @staticmethod
    def run_simulation(
        db: Session,
        frequency: str,
        template_name: str,
        month: int,
        day_of_week: int,
        overrides: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        active_model = SimulationService.get_active_model(db, frequency)
        if not active_model:
            raise ValueError("Nenhum modelo ativo encontrado. Ative um modelo primeiro.")

        frequency = active_model.model_pred_type
        original_dataset_type = active_model.dataset_selected  # Guardar o tipo original

        # Determinar o dataset_type para buscar o template correto
        if original_dataset_type == "pca":
            template_dataset = "full"
        else:
            template_dataset = original_dataset_type

        # 2. Obter template base alinhado com o dataset do modelo
        base_features = SimulationService.get_template(frequency, template_name, template_dataset)

        # 3. Validar e aplicar overrides
        if overrides:
            errors = SimulationService.validate_overrides(overrides)
            if errors:
                raise ValueError(f"Erro de validação: {'; '.join(errors)}")
            features = SimulationService.apply_overrides(base_features, overrides)
        else:
            features = base_features.copy()

        # 4. Adicionar features temporais
        features["month"] = month
        features["day_of_week"] = day_of_week

        # 5. PCA Flow: usar o template 'full' com 117 features
        if original_dataset_type == "pca":
            full_template = SimulationService.get_template(frequency, template_name, "full")
            if overrides:
                full_template.update(overrides)
            full_template["month"] = month
            full_template["day_of_week"] = day_of_week
            features_for_inference = full_template
            logger.info("PCA Flow: usando template 'full' com 117 features para PCA")
        else:
            features_for_inference = features

        # 6. Singleton
        engine = get_inference_engine()
        predicted_mw = engine.predict(frequency, features_for_inference)

        # 7. Top 2 drivers do modelo ativo
        if active_model.top2_drivers:
            top_drivers = [d.strip() for d in active_model.top2_drivers.split(",")]
        else:
            top_drivers = ["t2m", "day_of_week"]

        logger.info(
            f"Simulação concluída: {template_name}/{frequency}/{original_dataset_type} "
            f"-> {predicted_mw:.1f} MW | Drivers: {top_drivers}"
        )

        return {
            "predicted_mw": predicted_mw,
            "top_drivers": top_drivers,
        }
