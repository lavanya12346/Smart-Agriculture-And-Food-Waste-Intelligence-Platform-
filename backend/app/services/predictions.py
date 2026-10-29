from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LinearRegression


def _safe_linear_predict(values: list[float], horizon: int = 1) -> float:
    if len(values) < 2:
        return float(values[-1]) if values else 0.0
    x = np.arange(len(values), dtype=float).reshape(-1, 1)
    y = np.array(values, dtype=float)
    model = LinearRegression().fit(x, y)
    future_x = np.arange(len(values), len(values) + horizon, dtype=float).reshape(-1, 1)
    prediction = model.predict(future_x)
    return float(prediction[-1])


def estimate_demand(entries: list[dict[str, Any]], horizon_days: int = 7) -> dict[str, Any]:
    if not entries:
        return {
            "predicted_attendance": 0,
            "predicted_leftover_kg": 0,
            "trend": "stable",
            "note": "No recent demand data is available; showing a demo estimate.",
        }

    recent = entries[-7:]
    attendance = [float(e["actual_attendance"]) for e in recent]
    leftovers = [float(e["leftover_quantity_kg"]) for e in recent]
    predicted_attendance = max(0.0, _safe_linear_predict(attendance, 1))
    predicted_leftover = max(0.0, _safe_linear_predict(leftovers, 1))
    average_leftover = float(np.mean(leftovers)) if leftovers else 0.0
    trend = "rise" if predicted_leftover > average_leftover else "fall" if predicted_leftover < average_leftover else "stable"
    return {
        "predicted_attendance": round(predicted_attendance, 1),
        "predicted_leftover_kg": round(predicted_leftover, 2),
        "trend": trend,
        "note": "Demo estimate using a simple linear baseline on recent attendance and waste patterns.",
    }


def estimate_crop_price(history: list[float], horizon_days: int = 7) -> dict[str, Any]:
    if not history:
        return {"predicted_price": 0.0, "direction": "stable", "confidence": 0.25, "note": "No sufficient price history for a robust model; showing a sample estimate."}

    if len(history) < 3:
        current = float(history[-1])
        return {"predicted_price": current, "direction": "stable", "confidence": 0.35, "note": "Limited market data: demo estimate only."}

    x = np.arange(len(history), dtype=float).reshape(-1, 1)
    y = np.array(history, dtype=float)
    model = LinearRegression().fit(x, y)
    next_x = np.array([len(history)], dtype=float).reshape(-1, 1)
    predicted = float(model.predict(next_x)[0])
    current = float(history[-1])
    change = predicted - current
    direction = "rise" if change > 0.05 else "fall" if change < -0.05 else "stable"
    confidence = min(0.8, max(0.4, 0.55 + (len(history) / 30) * 0.25))
    return {
        "predicted_price": round(predicted, 2),
        "direction": direction,
        "confidence": round(confidence, 2),
        "note": "Demo estimate generated with a transparent linear trend model. This is not a guaranteed market forecast.",
    }
