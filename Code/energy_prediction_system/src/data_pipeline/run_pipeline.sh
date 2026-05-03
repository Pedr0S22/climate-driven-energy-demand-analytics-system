#!/bin/bash
set -e

# Garante que o PYTHONPATH inclui a raiz do código
export PYTHONPATH=$PYTHONPATH:/app/src

echo "--- Iniciando Ingestion ---"
python /app/src/data_pipeline/ingestion.py

echo "--- Iniciando Cleaning ---"
python /app/src/data_pipeline/cleaning.py

echo "--- Iniciando Feature Engineering ---"
python /app/src/data_pipeline/feature_engineering.py

echo "--- Iniciando Modeling ---"
python /app/src/data_pipeline/modeling.py

echo "--- Pipeline executado com sucesso! ---"
