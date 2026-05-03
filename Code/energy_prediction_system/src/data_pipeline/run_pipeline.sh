#!/bin/bash
set -e

echo "--- Iniciando Ingestion ---"
python /src/data_pipeline/ingestion.py


echo "--- Iniciando Cleaning ---"
python /src/data_pipeline/cleaning.py

echo "--- Iniciando Feature Engineering ---"
python /src/data_pipeline/feature_engineering.py

echo "--- Iniciando Modeling ---"
python /src/data_pipeline/modeling.py

echo "--- Pipeline concluído com sucesso! ---"