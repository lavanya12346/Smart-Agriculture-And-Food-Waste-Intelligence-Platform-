# AgriWaste Intelligence

AgriWaste Intelligence is a full-stack demo project that connects campus food-waste reduction with agricultural crop price intelligence. It helps canteen teams plan demand, identify waste patterns, and compare procurement options with local crop market trends.

## Features
- Smart canteen demand and waste tracking
- Baseline prediction for expected attendance and leftover quantity
- Historical and forecast crop price comparison
- Procurement planning page that aligns menu ingredients with market prices
- Demo login and seeded SQLite database
- FastAPI backend and React + TypeScript frontend

## Tech stack
- Frontend: React, TypeScript, Vite, Recharts
- Backend: Python, FastAPI, SQLAlchemy, SQLite
- Prediction: scikit-learn linear baseline
- Data persistence: SQLite file at `backend/agriwaste.db`

## Project structure
```text
PROJECT/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── predictions.py
│   ├── tests/
│   │   └── test_api.py
│   ├── requirements.txt
│   └── agriwaste.db (created at runtime)
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── index.html
├── README.md
└── .gitignore
```

## Backend setup
```bash
cd PROJECT/backend
python -m venv .venv
. .venv/bin/activate   # Linux/macOS
# or .\.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend setup
```bash
cd PROJECT/frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Demo login
- admin / admin123
- canteen / canteen123
- farmer / farmer123

## Model and data notes
- The demand and crop prediction modules use simple linear regression baselines on recent values.
- This is intentionally a demo system, so the project labels outputs as sample or estimate-based rather than production forecasts.
- Historical crop price values are seeded from example market data and can be replaced with a live market feed later via environment configuration.

## API docs
Once the backend is running, open:
- http://localhost:8000/docs
- http://localhost:8000/redoc

## Tests
```bash
cd PROJECT/backend
. .venv/bin/activate
pytest
```

## Limitations
- Predictions are sample estimates and should not be treated as guaranteed market or demand forecast values.
- No external market API integration is configured by default.
- This project is designed for a college demonstration and local development, not enterprise production deployment.
