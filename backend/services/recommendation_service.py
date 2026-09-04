from datetime import datetime
from sqlalchemy.orm import Session

from models import Location
from services.forecast_service import ForecastService


class RecommendationService:
    def __init__(self, session: Session):
        self.session = session
        self.forecasts = ForecastService(session)

    def recommend_alternatives(self, current_location_id, limit: int = 5):
        current = self.session.query(Location).filter(Location.id == current_location_id).first()
        if not current:
            return []

        current_forecast = self.forecasts.predict(current.id, datetime.utcnow())
        current_level = current_forecast.get("crowd_level")

        candidates = (
            self.session.query(Location)
            .filter(Location.is_active.is_(True), Location.category == current.category)
            .filter(Location.id != current.id)
            .all()
        )

        results = []
        for location in candidates:
            forecast = self.forecasts.predict(location.id, datetime.utcnow())
            if not forecast.get("available"):
                continue

            distance = current.distance_to(location)
            crowd = forecast.get("crowd_level")
            saving = (current_level - crowd) if current_level is not None and crowd is not None else 0
            score = max(0.0, min(100.0, 60 + saving * 12 - distance * 5))

            results.append({
                "location": location.to_dict(),
                "forecast": forecast,
                "distance_km": round(distance, 2),
                "recommendation_score": round(score, 2),
                "reason": "less_crowded" if saving > 0.25 else "alternative",
            })

        return sorted(results, key=lambda x: x["recommendation_score"], reverse=True)[:limit]
