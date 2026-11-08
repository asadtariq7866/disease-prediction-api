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

## Run with Docker

### 1. Get the code and train the model
`model.joblib` is not stored in the repo, so train it first.

```powershell
git clone https://github.com/asadtariq7866/disease-prediction-api.git
cd disease-prediction-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python train.py
```

On Linux or macOS, activate with `source .venv/bin/activate` instead.

### 2. Build the image
```
docker build -t disease-api .
```

### 3. Run the container
The model is mounted at runtime, not copied into the image.

PowerShell (Windows):
```powershell
docker run -d --name disease-api-c -p 8000:8000 -v "${PWD}/model.joblib:/app/model.joblib:ro" disease-api
```

Linux or macOS:
```bash
docker run -d --name disease-api-c -p 8000:8000 -v "$(pwd)/model.joblib:/app/model.joblib:ro" disease-api
```

Check it:
```
curl http://localhost:8000/health
```
Expected: `{"status":"ok","model_loaded":true}`. Docs: http://localhost:8000/docs

On Windows PowerShell use `curl.exe` instead of `curl`.

### Docker design decisions

**Non-root user.** The Dockerfile is multi-stage and the container runs as `appuser`, not root. `chown -R appuser /app` makes `appuser` the owner of `/app`. Without it, the background task could not write `predictions.log`, and that failure would be silent: the client still gets a prediction and the error only shows in the container logs.

**Model mounted at runtime.** The model changes every time I retrain, so it is mounted with `-v` instead of being baked into the image. After retraining I only replace `model.joblib` and restart the container; no rebuild is needed. The trade-off is that the image does not work on its own without the mount.

**Missing model fails at startup.** Running the image without the mount stops the container immediately:
```
docker run --name no-model disease-api
```
Exit code: `3` (shown by `docker ps -a` as `Exited (3)`).
Log message: `FileNotFoundError: No such file or directory: '/app/model.joblib'` followed by `Application startup failed. Exiting.`
Failing loudly at startup is better than a container that starts and then returns errors on every request.

### Image size
| Build | Size (DISK USAGE) |
|---|---|
| Without `.dockerignore` | 1.67 GB |
| With `.dockerignore` | 682 MB |

Without `.dockerignore`, `COPY . .` also copied my local `.venv` folder into the image. Excluding it, `__pycache__`, `.git`, `model.joblib` and `predictions.log` cut the size by about 1 GB.

Where the size goes (`docker history disease-api`): the installed Python packages (scikit-learn, pandas, numpy, scipy) are the largest layer at 391 MB. The Debian base adds about 88 MB, Python about 41 MB, and my own code is only about 258 kB. The ML packages ship precompiled and the slim base image has no compiler, so a multi-stage build removes very little here. Its real benefit in this project is running as a non-root user.

### Prediction log inside the container
After sending a prediction:
```
docker exec disease-api-c ls -l /app/predictions.log
```
Output: `-rw-r--r-- 1 appuser appuser 775 Nov  8 15:15 /app/predictions.log`
`docker exec disease-api-c whoami` prints `appuser`.

The log file lives inside the container. When the container is removed with `docker rm`, the log is deleted too, so this is only a temporary solution.