from fastapi.testclient import TestClient

from main import Features, app, ml_models

import pytest


@pytest.fixture(autouse=True)
def no_log_file(monkeypatch):
    monkeypatch.setattr("main.log_prediction", lambda features, result: None)


class FakeModel:
    def predict(self, X):
        return [1] * len(X)

    def predict_proba(self, X):
        return [[0.1, 0.9]] * len(X)


class FakeScaler:
    def transform(self, X):
        return X


# "with" ke bina TestClient lifespan nahi chalata, isliye fake model overwrite nahi hota
client = TestClient(app)
VALID = {name: 1.0 for name in Features.model_fields}


def setup_module():
    ml_models["classifier"] = FakeModel()
    ml_models["scaler"] = FakeScaler()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model_loaded": True}

def test_health_model_not_loaded():
    ml_models["classifier"] = None
    r = client.get("/health")
    assert r.json() == {"status": "ok", "model_loaded": False}
    ml_models["classifier"] = FakeModel()

def test_predict_valid():
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200
    assert r.json() == {"prediction": 1, "label": "benign", "probability": 0.9}


def test_predict_missing_field():
    bad = dict(VALID)
    del bad["mean_radius"]
    assert client.post("/predict", json=bad).status_code == 422


def test_predict_wrong_type():
    bad = {**VALID, "mean_radius": "abc"}
    assert client.post("/predict", json=bad).status_code == 422


def test_predict_negative_value_rejected():
    bad = {**VALID, "mean_area": -5}
    assert client.post("/predict", json=bad).status_code == 422


def test_batch_predict():
    r = client.post("/predict/batch", json=[VALID, VALID, VALID])
    assert r.status_code == 200
    assert len(r.json()) == 3
    assert all(item["prediction"] == 1 for item in r.json())


def test_batch_empty_rejected():
    assert client.post("/predict/batch", json=[]).status_code == 422