from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated

import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

# Sab features physical measurements hain, negative nahi ho sakti -> reject (422)
NonNeg = Annotated[float, Field(ge=0)]

LABELS = {0: "malignant", 1: "benign"}
ml_models = {}


class Features(BaseModel):
    mean_radius: NonNeg
    mean_texture: NonNeg
    mean_perimeter: NonNeg
    mean_area: NonNeg
    mean_smoothness: NonNeg
    mean_compactness: NonNeg
    mean_concavity: NonNeg
    mean_concave_points: NonNeg
    mean_symmetry: NonNeg
    mean_fractal_dimension: NonNeg
    radius_error: NonNeg
    texture_error: NonNeg
    perimeter_error: NonNeg
    area_error: NonNeg
    smoothness_error: NonNeg
    compactness_error: NonNeg
    concavity_error: NonNeg
    concave_points_error: NonNeg
    symmetry_error: NonNeg
    fractal_dimension_error: NonNeg
    worst_radius: NonNeg
    worst_texture: NonNeg
    worst_perimeter: NonNeg
    worst_area: NonNeg
    worst_smoothness: NonNeg
    worst_compactness: NonNeg
    worst_concavity: NonNeg
    worst_concave_points: NonNeg
    worst_symmetry: NonNeg
    worst_fractal_dimension: NonNeg


class Prediction(BaseModel):
    prediction: int
    label: str
    probability: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading model...")
    bundle = joblib.load(Path(__file__).parent / "model.joblib")
    ml_models["classifier"] = bundle["model"]
    ml_models["scaler"] = bundle["scaler"]
    ml_models["feature_names"] = bundle["feature_names"]
    ml_models["metrics"] = bundle["metrics"]
    yield
    ml_models.clear()


app = FastAPI(title="Disease Prediction API", lifespan=lifespan)


def log_prediction(features: dict, result: int) -> None:
    with open("predictions.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} prediction={result} features={features}\n")


def run_inference(rows):
    scaled = ml_models["scaler"].transform(rows)
    model = ml_models["classifier"]
    return model.predict(scaled), model.predict_proba(scaled)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/model/info")
def model_info():
    return {
        "features": ml_models["feature_names"],
        "metrics": ml_models["metrics"],
    }


@app.post("/predict", response_model=Prediction)
def predict(features: Features, background_tasks: BackgroundTasks):
    row = [list(features.model_dump().values())]
    preds, probas = run_inference(row)
    pred = int(preds[0])
    proba = float(probas[0][pred])
    background_tasks.add_task(log_prediction, features.model_dump(), pred)
    return Prediction(prediction=pred, label=LABELS[pred], probability=proba)


@app.post("/predict/batch", response_model=list[Prediction])
def predict_batch(
    items: Annotated[list[Features], Field(min_length=1)],
    background_tasks: BackgroundTasks,
):
    df = pd.DataFrame([item.model_dump() for item in items])
    preds, probas = run_inference(df.values)
    results = []
    for i, p in enumerate(preds):
        p = int(p)
        results.append(
            Prediction(prediction=p, label=LABELS[p], probability=float(probas[i][p]))
        )
        background_tasks.add_task(log_prediction, items[i].model_dump(), p)
    return results