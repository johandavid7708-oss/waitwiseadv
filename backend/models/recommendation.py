from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    current_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"))
    recommended_location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    
    # Scores
    wait_time_savings = Column(Integer)  # minutes
    distance_km = Column(Float)
    travel_time_minutes = Column(Integer)
    recommendation_score = Column(Float)  # 0-100
    
    # Reasoning
    reason = Column(String(100))  # 'less_crowded', 'closer', 'better_time', etc
    
    # Feedback
    was_helpful = Column(Boolean)
    user_chose = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    current_location = relationship(
        "Location",
        foreign_keys=[current_location_id],
        backref="current_recommendations"
    )
    recommended_location = relationship(
        "Location",
        foreign_keys=[recommended_location_id],
        backref="recommendations_for"
    )

    __table_args__ = (
        Index("idx_recommendations_user", "user_id"),
        Index("idx_recommendations_current_location", "current_location_id"),
    )

    def __repr__(self):
        return f"<Recommendation user_id={self.user_id} score={self.recommendation_score}>"

    def calculate_score(self, 
                       wait_time_diff: float,
                       distance_weight: float = 0.2,
                       time_weight: float = 0.5,
                       crowd_weight: float = 0.3) -> float:
        """
        Calculate recommendation score (0-100).
        
        Factors:
        - Wait time savings (50%)
        - Distance (20%)
        - Travel time (30%)
        """
        # Normalize wait time savings (max 30 min savings = 100 points)
        wait_score = min(100, (wait_time_diff / 30) * 100)
        
        # Distance score (prefer closer, 5km = 100)
        distance_score = max(0, 100 - (self.distance_km * 20)) if self.distance_km else 50
        
        # Travel time score (prefer quick, 30 min = 100)
        travel_score = max(0, 100 - (self.travel_time_minutes * 3.33)) if self.travel_time_minutes else 50
        
        # Weighted score
        score = (wait_score * 0.5) + (distance_score * distance_weight) + (travel_score * time_weight)
        
        self.recommendation_score = min(100, max(0, score))
        return self.recommendation_score

    def set_reason(self):
        """Determine and set the reason for recommendation."""
        if not self.recommendation_score:
            return
        
        if self.wait_time_savings and self.wait_time_savings > 10:
            self.reason = "less_crowded"
        elif self.distance_km and self.distance_km < 0.5:
            self.reason = "closer"
        elif self.travel_time_minutes and self.travel_time_minutes < 10:
            self.reason = "quicker_travel"
        else:
            self.reason = "better_alternative"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "current_location_id": str(self.current_location_id) if self.current_location_id else None,
            "recommended_location_id": str(self.recommended_location_id),
            "wait_time_savings": self.wait_time_savings,
            "distance_km": self.distance_km,
            "travel_time_minutes": self.travel_time_minutes,
            "recommendation_score": self.recommendation_score,
            "reason": self.reason,
            "was_helpful": self.was_helpful,
            "user_chose": self.user_chose,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
