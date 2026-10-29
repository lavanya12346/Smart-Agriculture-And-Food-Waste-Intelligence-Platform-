from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    role: str = "admin"
    full_name: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LoginRequest(BaseModel):
    username: str
    password: str


class MealEntryBase(BaseModel):
    entry_date: date
    meal_type: str
    menu_name: str
    expected_attendance: int = 0
    actual_attendance: int = 0
    meals_prepared: int = 0
    meals_served: int = 0
    leftover_quantity_kg: float = 0.0
    donated_kg: float = 0.0
    reused_kg: float = 0.0
    discarded_kg: float = 0.0
    notes: Optional[str] = None


class MealEntryCreate(MealEntryBase):
    pass


class MealEntryRead(MealEntryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[date] = None


class ProcurementPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ingredient_name: str
    crop_name: Optional[str]
    market_name: Optional[str]
    target_date: date
    required_kg: float
    estimated_cost: float
    expected_demand: int
    price_per_unit: float
    unit: str
    note: Optional[str]
