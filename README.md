# Disease Prediction API

FastAPI service that serves a Breast Cancer (malignant/benign) classifier.

## Retrain the model
python train.py

This trains a Logistic Regression on the scikit-learn Breast Cancer dataset
(80/20 split, StandardScaler) and saves `model.joblib` (model + scaler).

## Run the API
uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs

## Endpoints
- GET /health
- GET /model/info
- POST /predict (30 features -> prediction, label, probability)
- POST /predict/batch (list of feature sets -> list of predictions)

## Model performance (test set)
| Metric | Score |
|---|---|
| Accuracy | 0.9737 |
| Precision | 0.9722 |
| Recall | 0.9859 |
| F1 | 0.979 |

## Out-of-range input decision
All features are physical measurements, so negative values are rejected
with 422. Very large positive values are accepted, but the model
extrapolates beyond its training range, so such predictions are unreliable.

## Tests
pytest
Tests use a fake model, so they don't need `model.joblib`.

## Notes
Every prediction is logged to `predictions.log` via a background task,
so the response is not delayed by logging.