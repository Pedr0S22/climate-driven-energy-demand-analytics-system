import joblib


class InferenceEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InferenceEngine, cls).__new__(cls)
            cls._instance.active_model = None
            cls._instance.scaler = None
            cls._instance.pca = None
        return cls._instance

    def load_active_model(self, db_model_record):
        """Carrega os arquivos .joblib em memória (RAM)"""
        print(f"Carregando novo modelo: {db_model_record.name}")
        self.active_model = joblib.load(db_model_record.model_path)
        self.scaler = joblib.load(db_model_record.scaler_path)

        if db_model_record.pca_path:
            self.pca = joblib.load(db_model_record.pca_path)
        else:
            self.pca = None

# Para usar: engine = InferenceEngine()
