from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(40), default="admin")
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="grain")
    unit: Mapped[str] = mapped_column(String(40), default="quintal")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    price_history: Mapped[list["CropPriceHistory"]] = relationship(back_populates="crop")
    predictions: Mapped[list["CropPricePrediction"]] = relationship(back_populates="crop")


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    location: Mapped[str] = mapped_column(String(80), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")

    price_history: Mapped[list["CropPriceHistory"]] = relationship(back_populates="market")
    predictions: Mapped[list["CropPricePrediction"]] = relationship(back_populates="market")


class CropPriceHistory(Base):
    __tablename__ = "crop_price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("crops.id"), nullable=False)
    market_id: Mapped[int] = mapped_column(Integer, ForeignKey("markets.id"), nullable=False)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_per_quintal: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(80), default="sample-data")

    crop: Mapped[Crop] = relationship(back_populates="price_history")
    market: Mapped[Market] = relationship(back_populates="price_history")


class CropPricePrediction(Base):
    __tablename__ = "crop_price_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("crops.id"), nullable=False)
    market_id: Mapped[int] = mapped_column(Integer, ForeignKey("markets.id"), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_price: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=7)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str] = mapped_column(Text, default="Demo estimate based on recent trend")

    crop: Mapped[Crop] = relationship(back_populates="predictions")
    market: Mapped[Market] = relationship(back_populates="predictions")


class MealEntry(Base):
    __tablename__ = "meal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    menu_name: Mapped[str] = mapped_column(String(120), nullable=False)
    expected_attendance: Mapped[int] = mapped_column(Integer, default=0)
    actual_attendance: Mapped[int] = mapped_column(Integer, default=0)
    meals_prepared: Mapped[int] = mapped_column(Integer, default=0)
    meals_served: Mapped[int] = mapped_column(Integer, default=0)
    leftover_quantity_kg: Mapped[float] = mapped_column(Float, default=0.0)
    donated_kg: Mapped[float] = mapped_column(Float, default=0.0)
    reused_kg: Mapped[float] = mapped_column(Float, default=0.0)
    discarded_kg: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProcurementPlan(Base):
    __tablename__ = "procurement_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    crop_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    market_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    required_kg: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    expected_demand: Mapped[int] = mapped_column(Integer, default=0)
    price_per_unit: Mapped[float] = mapped_column(Float, default=0.0)
    unit: Mapped[str] = mapped_column(String(40), default="kg")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
