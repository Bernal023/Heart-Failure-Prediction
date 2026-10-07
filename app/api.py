import json
from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

APP_DIR = Path(__file__).resolve().parent
model = joblib.load(APP_DIR / "model.joblib")
FEATURES = json.loads((APP_DIR / "features.json").read_text())["features"]

app = FastAPI(title="Heart Failure Prediction API")


class Input(BaseModel):
    features: Dict[str, Any]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(data: Input):
    row = pd.DataFrame([data.features]).reindex(columns=FEATURES)
    proba = float(model.predict_proba(row)[0][1])
    return {
        "heart_disease_probability": proba,
        "prediction": int(proba > 0.5),
    }
