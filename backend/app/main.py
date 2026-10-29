from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Crop, CropPriceHistory, CropPricePrediction, Market, MealEntry, ProcurementPlan, User
from .schemas import LoginRequest, MealEntryCreate, MealEntryRead
from .seed import seed_database
from .services.predictions import estimate_crop_price, estimate_demand

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgriWaste Intelligence", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AgriWaste Intelligence"}


@app.post("/api/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username, User.password == payload.password).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "token": f"demo-token-{user.id}",
        "user": {"id": user.id, "username": user.username, "role": user.role, "full_name": user.full_name},
    }


@app.get("/api/admin/data")
def get_admin_data(db: Session = Depends(get_db)):
    crops = db.query(Crop).all()
    markets = db.query(Market).all()
    users = db.query(User).all()
    return {
        "crops": [{"id": c.id, "name": c.name, "category": c.category, "unit": c.unit} for c in crops],
        "markets": [{"id": m.id, "name": m.name, "location": m.location, "currency": m.currency} for m in markets],
        "users": [{"id": u.id, "username": u.username, "role": u.role, "full_name": u.full_name} for u in users],
    }


@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_meals = db.query(func.sum(MealEntry.meals_served)).scalar() or 0
    total_waste = db.query(func.sum(MealEntry.leftover_quantity_kg)).scalar() or 0
    entries = db.query(MealEntry).order_by(MealEntry.entry_date.desc()).all()
    waste_pct_raw = [
        (entry.leftover_quantity_kg / max(1, entry.meals_prepared)) * 100
        for entry in entries
        if entry.meals_prepared > 0
    ]
    average_waste_pct = round(sum(waste_pct_raw) / len(waste_pct_raw), 2) if waste_pct_raw else 0.0
    return {
        "summary": {
            "meals_served": int(total_meals),
            "food_wasted_kg": round(float(total_waste), 2),
            "waste_percentage": average_waste_pct,
            "estimated_waste_cost": round(float(total_waste) * 210, 2),
            "active_users": db.query(User).count(),
        },
        "trend_series": [
            {
                "date": entry.entry_date.isoformat(),
                "served": entry.meals_served,
                "waste": entry.leftover_quantity_kg,
                "attendance": entry.actual_attendance,
            }
            for entry in db.query(MealEntry).order_by(MealEntry.entry_date.asc()).limit(10).all()
        ],
        "recommendations": [
            "Reduce breakfast preparation by 8% on low-attendance days.",
            "Veg Biryani and curry rice repeatedly show the highest waste.",
            "Review donation logs to reclaim surplus value before disposal.",
        ],
    }


@app.get("/api/waste/records")
def get_waste_records(db: Session = Depends(get_db)):
    entries = db.query(MealEntry).order_by(MealEntry.entry_date.desc()).all()
    return [
        {
            "id": e.id,
            "entry_date": e.entry_date.isoformat(),
            "meal_type": e.meal_type,
            "menu_name": e.menu_name,
            "expected_attendance": e.expected_attendance,
            "actual_attendance": e.actual_attendance,
            "meals_prepared": e.meals_prepared,
            "meals_served": e.meals_served,
            "leftover_quantity_kg": e.leftover_quantity_kg,
            "donated_kg": e.donated_kg,
            "reused_kg": e.reused_kg,
            "discarded_kg": e.discarded_kg,
            "notes": e.notes,
        }
        for e in entries
    ]


@app.post("/api/waste/records", response_model=MealEntryRead)
def create_waste_record(payload: MealEntryCreate, db: Session = Depends(get_db)):
    entry = MealEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.post("/api/waste/predict")
def predict_waste(payload: dict[str, Any], db: Session = Depends(get_db)):
    menu_name = payload.get("menu_name")
    selected_date = payload.get("selected_date")
    if not menu_name:
        raise HTTPException(status_code=400, detail="menu_name is required")
    relevant_entries = db.query(MealEntry).filter(MealEntry.menu_name == menu_name).order_by(MealEntry.entry_date.asc()).all()
    output = estimate_demand([
        {
            "actual_attendance": e.actual_attendance,
            "meals_prepared": e.meals_prepared,
            "leftover_quantity_kg": e.leftover_quantity_kg,
        }
        for e in relevant_entries
    ])
    output["selected_date"] = selected_date or date.today().isoformat()
    output["menu_name"] = menu_name
    return output


@app.get("/api/crops")
def list_crops(db: Session = Depends(get_db)):
    crops = db.query(Crop).all()
    return [{"id": c.id, "name": c.name, "category": c.category, "unit": c.unit} for c in crops]


@app.get("/api/crops/{crop_id}/prices")
def get_crop_prices(crop_id: int, market_id: int = Query(default=None), horizon_days: int = 7, db: Session = Depends(get_db)):
    crop = db.query(Crop).filter(Crop.id == crop_id).first()
    if not crop:
        raise HTTPException(404, "Crop not found")
    market = db.query(Market).filter(Market.id == market_id).first() if market_id else db.query(Market).first()
    if not market:
        raise HTTPException(404, "Market not found")
    history = db.query(CropPriceHistory).filter(CropPriceHistory.crop_id == crop_id, CropPriceHistory.market_id == market.id).order_by(CropPriceHistory.price_date.asc()).all()
    series = [{"date": item.price_date.isoformat(), "price": float(item.price_per_quintal)} for item in history]
    current = float(history[-1].price_per_quintal) if history else 0.0
    values = [float(item.price_per_quintal) for item in history]
    forecast = estimate_crop_price(values, horizon_days)
    prediction = CropPricePrediction(
        crop_id=crop.id,
        market_id=market.id,
        forecast_date=date.today() + timedelta(days=horizon_days),
        predicted_price=forecast["predicted_price"],
        direction=forecast["direction"],
        horizon_days=horizon_days,
        confidence=forecast["confidence"],
        note=forecast["note"],
    )
    db.add(prediction)
    db.commit()
    return {
        "crop_name": crop.name,
        "market_name": market.name,
        "current_price": current,
        "forecast": {
            "date": prediction.forecast_date.isoformat(),
            "predicted_price": prediction.predicted_price,
            "direction": prediction.direction,
            "confidence": prediction.confidence,
            "note": prediction.note,
        },
        "history": series,
        "demo_notice": "Sample market data is used in this demo; predictions are baseline estimates and not guaranteed market outcomes.",
    }


@app.get("/api/procurement/planning")
def get_procurement_plans(db: Session = Depends(get_db)):
    plans = db.query(ProcurementPlan).order_by(ProcurementPlan.target_date.asc()).all()
    return [
        {
            "id": p.id,
            "ingredient_name": p.ingredient_name,
            "crop_name": p.crop_name,
            "market_name": p.market_name,
            "target_date": p.target_date.isoformat(),
            "required_kg": p.required_kg,
            "estimated_cost": p.estimated_cost,
            "expected_demand": p.expected_demand,
            "price_per_unit": p.price_per_unit,
            "unit": p.unit,
            "note": p.note,
        }
        for p in plans
    ]


@app.get("/api/markets")
def list_markets(db: Session = Depends(get_db)):
    markets = db.query(Market).all()
    return [{"id": m.id, "name": m.name, "location": m.location, "currency": m.currency} for m in markets]


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
