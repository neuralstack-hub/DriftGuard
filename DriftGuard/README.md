# DriftGuard — Automated ML Model Monitoring & Self-Healing Platform

DriftGuard is an end-to-end MLOps platform that monitors deployed machine learning models, detects input data drift, triggers automated retraining on **labelled** data, evaluates candidate models against the active production model on a **fixed holdout validation set**, and supports safe model promotion and rollback.

> **Important Distinction:** Data drift indicates that incoming input feature distributions have shifted relative to training data. It does **not** automatically mean model accuracy has degraded; true performance degradation can only be confirmed when ground-truth labels arrive.

---

## 1. Use Case & Dataset
- **Use Case**: Hourly PM2.5 air-quality prediction (`ug/m³`) using meteorological observations.
- **Dataset**: [Beijing PM2.5 Data Set](https://archive.ics.uci.edu/dataset/381/beijing+pm2+5+data) (UCI Machine Learning Repository, DOI: `10.24432/C5JS49`, License: **CC BY 4.0**).
- **File**: `PRSA_data_2010.1.1-2014.12.31.csv` (43,824 hourly rows, 2010–2014).
- **Features**: `month`, `day`, `hour`, `DEWP` (Dew Point), `TEMP` (Temperature), `PRES` (Pressure), `cbwd` (Combined wind direction: `NE`, `NW`, `SE`, `cv`), `Iws` (Cumulated wind speed), `Is` (Snow hours), `Ir` (Rain hours).
- **Target**: `pm2.5` concentration (`ug/m³`).
- **Chronological Split (Leakage-Free)**:
  - **2010–2012**: Reference & initial training set (`Model v1`).
  - **2013**: Labelled retraining pool / production stream.
  - **2014**: Fixed holdout validation set (used to compare all candidate models against the active model).

Download the official dataset into `data/raw/` before training:
```bash
python scripts/download_dataset.py
```

---

## 2. Project Structure
```text
DriftGuard/
├── .github/workflows/
│   ├── ci.yml
│   ├── train-model.yml
│   └── drift-retrain.yml
├── artifacts/
│   ├── models/                # Saved .joblib models & registry.json
│   └── monitoring/            # Drift, retraining & deployment history.json
├── backend/
│   ├── app/                   # FastAPI routes, schemas, config & services
│   ├── ml/                    # Preprocessing, training, evaluation, drift & retraining
│   ├── tests/                 # Unit & integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── data/
│   ├── raw/                   # PRSA_data_2010.1.1-2014.12.31.csv
│   └── processed/             # Chronological splits
├── frontend/                  # React + Vite + Tailwind + Recharts dashboard
├── scripts/
│   └── download_dataset.py
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 3. Local Setup & Running

### Prerequisites
- Python 3.11+
- Node.js 18+ / npm
- Docker & Docker Compose (optional, for containerized run)

### Step 1: Configure Environment
```bash
cp .env.example .env
```

### Step 2: Download Dataset
```bash
python scripts/download_dataset.py
```

### Step 3: Run Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
cd ..
PYTHONPATH=. uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs will be available at `http://localhost:8000/docs`.

### Step 4: Run Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Step 5: Run with Docker Compose
```bash
docker compose up --build
```

---

## 4. Running Tests
```bash
PYTHONPATH=. pytest backend/tests -v
# or using Python's built-in unittest:
PYTHONPATH=. python3 -m unittest discover -s backend/tests -v
```

---

## 5. GitHub Actions CI/CD & Secure Triggering
1. **CI (`ci.yml`)**: Runs `pytest` and builds the React frontend on every push or pull request.
2. **Manual Training (`train-model.yml`)**: Downloads the dataset and trains baseline `Model v1`.
3. **Drift-Triggered Retraining (`drift-retrain.yml`)**: Listens for `repository_dispatch` (`event_type: drift-detected`).
   - **How the backend triggers it securely**: When `GITHUB_TOKEN` (a fine-grained PAT with `Actions: write` / `Contents: write` scope), `GITHUB_OWNER`, and `GITHUB_REPO` are set in `.env`, `MonitoringService.trigger_github_actions()` sends an authenticated `POST https://api.github.com/repos/{owner}/{repo}/dispatches` request. Secrets are never hardcoded.
   - **Deployment note**: Building the Docker image in GitHub Actions validates the container build; deploying it to production requires pushing to a container registry (e.g., GHCR/Docker Hub) and updating your target host/orchestrator.

---

## 6. End-to-End Demonstration Walkthrough
1. Open the dashboard at `http://localhost:5173`.
2. On **Overview**, click **Initialize / Train Model v1** to preprocess the Beijing PM2.5 dataset and train `Model v1` (`RandomForestRegressor`).
3. Test **Live PM2.5 Prediction** with sample weather inputs.
4. Go to **Simulation**, keep auto-retrain enabled, and click **Simulate Drift** to shift meteorological distributions (`TEMP`, `DEWP`, `PRES`, `Iws`), detect drift (`KS-test` + `PSI`), and trigger candidate retraining (`v2`).
5. Toggle **Simulate degraded candidate** and click **Simulate Drift** again to verify that a worse candidate (`v3`) is **rejected** while the active model remains deployed.
6. Go to **Model Management** to inspect version metrics and test **Rollback to Previous**.
7. Check **Pipeline Monitoring** to view retraining history, deployment logs, rollback history, and GitHub Actions dispatch status.
