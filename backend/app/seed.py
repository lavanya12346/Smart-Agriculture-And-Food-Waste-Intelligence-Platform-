from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from .models import Crop, CropPriceHistory, Market, MealEntry, ProcurementPlan, User


def seed_database(db: Session) -> None:
    if db.query(User).count() > 0:
        return

    # Ensure the demo dataset is always fresh during tests and local runs.
    db.query(ProcurementPlan).delete()
    db.query(MealEntry).delete()
    db.query(CropPriceHistory).delete()

    admin = User(username="admin", password="admin123", role="admin", full_name="Campus Admin")
    manager = User(username="canteen", password="canteen123", role="canteen_manager", full_name="Canteen Manager")
    buyer = User(username="farmer", password="farmer123", role="farmer_buyer", full_name="Farmer Buyer")
    db.add_all([admin, manager, buyer])

    rice = Crop(name="Rice", category="grain", unit="quintal")
    wheat = Crop(name="Wheat", category="grain", unit="quintal")
    tomato = Crop(name="Tomato", category="vegetable", unit="quintal")
    onion = Crop(name="Onion", category="vegetable", unit="quintal")
    db.add_all([rice, wheat, tomato, onion])
    db.flush()

    coimbatore = Market(name="Coimbatore", location="Tamil Nadu", currency="INR")
    madurai = Market(name="Madurai", location="Tamil Nadu", currency="INR")
    trichy = Market(name="Trichy", location="Tamil Nadu", currency="INR")
    db.add_all([coimbatore, madurai, trichy])
    db.flush()

    today = date.today()
    for crop in [rice, wheat, tomato, onion]:
        for market in [coimbatore, madurai, trichy]:
            base_price = {rice: 2180, wheat: 2450, tomato: 3200, onion: 2800}[crop]
            for i in range(14):
                price_date = today - timedelta(days=13 - i)
                drift = i * 24 if crop in [rice, wheat] else i * 30
                seasonal = 85 if crop == tomato else 70 if crop == onion else 45
                price = base_price + drift + (i % 3) * 16 - seasonal
                if market.name == "Madurai":
                    price += 80
                if market.name == "Trichy":
                    price -= 40
                db.add(
                    CropPriceHistory(
                        crop_id=crop.id,
                        market_id=market.id,
                        price_date=price_date,
                        price_per_quintal=max(1500.0, float(price)),
                        source="sample-data",
                    )
                )

    menu_entries = [
        (today - timedelta(days=6), "Breakfast", "Idli + Sambar", 320, 310, 420, 400, 18.5, 4, 8, 6.5, "Moderate variation"),
        (today - timedelta(days=5), "Lunch", "Rice + Sambar", 420, 405, 520, 490, 24.2, 5.2, 10.8, 8.2, "Rice portion slightly high"),
        (today - timedelta(days=4), "Dinner", "Chapati + Dal", 290, 300, 360, 310, 21.5, 6.0, 7.0, 8.5, "Demand stable"),
        (today - timedelta(days=3), "Breakfast", "Pongal", 310, 295, 370, 290, 17.0, 3.5, 5.0, 8.5, "Overflow from previous order"),
        (today - timedelta(days=2), "Lunch", "Veg Biryani", 350, 328, 420, 340, 29.0, 7.5, 11.0, 10.5, "Repeated waste for biryani"),
        (today - timedelta(days=1), "Dinner", "Curry Rice", 360, 370, 440, 360, 26.0, 6.2, 8.5, 11.3, "Prepared more than needed"),
        (today, "Lunch", "Rice + Curry", 390, 400, 500, 420, 23.5, 5.8, 9.5, 8.2, "Strong lunch demand"),
    ]
    for row in menu_entries:
        db.add(
            MealEntry(
                entry_date=row[0],
                meal_type=row[1],
                menu_name=row[2],
                expected_attendance=row[3],
                actual_attendance=row[4],
                meals_prepared=row[5],
                meals_served=row[6],
                leftover_quantity_kg=row[7],
                donated_kg=row[8],
                reused_kg=row[9],
                discarded_kg=row[10],
                notes=row[11],
            )
        )

    procurement_rows = [
        ("Rice", "Rice", "Coimbatore", today + timedelta(days=2), 280, 58000, 360, 210, "kg", "Based on forecasted lunch demand and falling rice prices"),
        ("Tomato", "Tomato", "Madurai", today + timedelta(days=3), 180, 54000, 280, 300, "kg", "Tomato prices are trending upward in nearby markets"),
        ("Onion", "Onion", "Trichy", today + timedelta(days=4), 160, 44000, 260, 280, "kg", "Procure ahead of weekend demand"),
    ]
    for crop_name, ingredient_name, market_name, target_date, required_kg, est_cost, expected_demand, price_per_unit, unit, note in procurement_rows:
        db.add(
            ProcurementPlan(
                ingredient_name=ingredient_name,
                crop_name=crop_name,
                market_name=market_name,
                target_date=target_date,
                required_kg=required_kg,
                estimated_cost=est_cost,
                expected_demand=expected_demand,
                price_per_unit=price_per_unit,
                unit=unit,
                note=note,
            )
        )

    db.commit()
