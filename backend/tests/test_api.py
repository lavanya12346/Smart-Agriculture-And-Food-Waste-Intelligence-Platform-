from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_success():
    response = client.post("/api/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "admin"


def test_dashboard_metrics():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert payload["summary"]["meals_served"] > 0


def test_crop_price_endpoint():
    response = client.get("/api/crops/1/prices", params={"market_id": 1, "horizon_days": 7})
    assert response.status_code == 200
    payload = response.json()
    assert "forecast" in payload
    assert payload["history"]


def test_waste_prediction_baseline():
    response = client.post("/api/waste/predict", json={"menu_name": "Rice + Sambar", "selected_date": "2026-10-29"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["menu_name"] == "Rice + Sambar"
    assert "predicted_leftover_kg" in payload
