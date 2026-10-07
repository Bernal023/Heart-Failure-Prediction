# Heart Failure Prediction (MLOps local)

Modelo de clasificación binaria que predice el riesgo de falla cardíaca
(`HeartDisease`) con el dataset *Heart Failure Prediction* de Kaggle.

## Resultado
- Modelo final: **Random_Forest** (elegido por AUC en validación cruzada)
- AUC en prueba: 0.929
- Accuracy en prueba: 0.880

## Estructura
- `app/`: API FastAPI (`api.py`), `model.joblib` y `features.json`
- `docker/`: `Dockerfile` y `requirements.txt`
- `k8s/`: `deployment.yaml` y `service.yaml`
- `tests/`: pruebas de la API
- `.github/workflows/ci.yml`: lint y pruebas en cada push
- `models/` y `results/`: un archivo por modelo entrenado (checkpoints)
- `figures/`: curvas ROC y matrices de confusión
- `drift_report.html`: reporte de deriva de datos (Evidently)

## Uso
```
docker build -t heart-api -f docker/Dockerfile .
docker run -p 8000:8000 heart-api
curl -X POST localhost:8000/predict -H "Content-Type: application/json" \
     -d '{"features": {"Age": 46, "Sex": "M", "ChestPainType": "ASY", "RestingBP": 115.0, "Cholesterol": null, "FastingBS": 0, "RestingECG": "Normal", "MaxHR": 113, "ExerciseAngina": "Y", "Oldpeak": 1.5, "ST_Slope": "Flat"}}'
```
