from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import Location
from ml import CrowdPredictionEngine
from services.crowd_service import CrowdService


class ForecastService:
    """Hybrid ML + historical + current-condition forecasting."""

    def __init__(self, session: Session):
        self.session = session
        self.crowd_service = CrowdService(session)
        self.engine = CrowdPredictionEngine()

    def _historical_fallback(self, location_id, forecast_time: datetime):
        reports = self.crowd_service.get_verified_reports(location_id, limit=500)
        if not reports:
            return {"available": False, "reason": "No verified historical data", "prediction_method": "none"}

        same_hour = [r for r in reports if r.created_at and abs(r.created_at.hour - forecast_time.hour) <= 1]
        sample = same_hour if len(same_hour) >= 3 else reports
        crowds = [r.crowd_level for r in sample if r.crowd_level is not None]
        waits = [r.wait_time_minutes for r in sample if r.wait_time_minutes is not None]

        return {
            "available": bool(crowds),
            "crowd_level": round(sum(crowds) / len(crowds), 3) if crowds else None,
            "wait_time_minutes": round(sum(waits) / len(waits), 2) if waits else None,
            "confidence": min(0.75, 0.25 + len(sample) * 0.02),
            "samples": len(sample),
            "prediction_method": "historical",
        }

    def predict(self, location_id, forecast_time: datetime):
        location = self.session.query(Location).filter(Location.id == location_id).first()
        if not location:
            return {"available": False, "reason": "Location not found"}

        try:
            result = self.engine.predict(self.session, str(location_id), forecast_time)
            prediction = {
                "available": True,
                "crowd_level": float(result.predicted_crowd_level),
                "wait_time_minutes": result.predicted_wait_time,
                "confidence": float(result.confidence_score),
                "reasoning": result.reasoning,
                "prediction_method": "machine_learning",
            }
        except Exception:
            prediction = self._historical_fallback(location_id, forecast_time)

        if not prediction.get("available"):
            return prediction

        current = self.crowd_service.get_current_crowd(location_id, hours=2)
        if current.get("available") and current.get("crowd_level") is not None:
            hours_ahead = max(0.0, (forecast_time - datetime.utcnow()).total_seconds() / 3600)
            current_weight = max(0.10, min(0.70, 0.70 - hours_ahead * 0.08))
            prediction["crowd_level"] = round(
                current["crowd_level"] * current_weight
                + prediction["crowd_level"] * (1 - current_weight),
                3,
            )
            prediction["current_conditions_used"] = True
            prediction["current_conditions_weight"] = round(current_weight, 3)

        prediction.update({
            "location_id": str(location.id),
            "location_name": location.name,
            "forecast_time": forecast_time.isoformat(),
        })
        return prediction

    def get_location_forecast(self, location_id, hours: int = 6):
        now = datetime.utcnow()
        forecasts = [self.predict(location_id, now + timedelta(hours=i)) for i in range(1, hours + 1)]
        forecasts = [f for f in forecasts if f.get("available")]
        best = min(forecasts, key=lambda f: f["crowd_level"]) if forecasts else None
        return {
            "available": bool(forecasts),
            "forecast_hours": hours,
            "current": self.crowd_service.get_current_crowd(location_id),
            "trend": self.crowd_service.get_crowd_trend(location_id),
            "forecasts": forecasts,
            "best_time": best,
        }
