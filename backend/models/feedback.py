from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="SET NULL"))
    
    # Feedback details
    feedback_type = Column(String(50))  # 'prediction_accurate', 'recommendation_helpful', etc
    rating = Column(Integer)  # 1-5
    comment = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="feedback")
    prediction = relationship("Prediction", back_populates="feedback")

    __table_args__ = (
        Index("idx_feedback_prediction", "prediction_id"),
        Index("idx_feedback_user", "user_id"),
    )

    def __repr__(self):
        return f"<UserFeedback user_id={self.user_id} rating={self.rating}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "prediction_id": str(self.prediction_id) if self.prediction_id else None,
            "feedback_type": self.feedback_type,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }


class ModelPerformance(Base):
    __tablename__ = "model_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model info
    model_version = Column(String(50))
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"))
    
    # Metrics
    mean_absolute_error = Column(Float)
    root_mean_square_error = Column(Float)
    r_squared = Column(Float)
    accuracy_percentage = Column(Float)
    
    # Period
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    predictions_evaluated = Column(Integer)

    # Relationships
    location = relationship("Location")

    __table_args__ = (
        Index("idx_model_perf_version_location", "model_version", "location_id"),
    )

    def __repr__(self):
        return f"<ModelPerformance version={self.model_version} acc={self.accuracy_percentage:.1f}%>"

    def is_better_than(self, other: "ModelPerformance") -> bool:
        """Check if this model performs better than another."""
        if not self.accuracy_percentage or not other.accuracy_percentage:
            return False
        return self.accuracy_percentage > other.accuracy_percentage

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "model_version": self.model_version,
            "location_id": str(self.location_id) if self.location_id else None,
            "mean_absolute_error": self.mean_absolute_error,
            "root_mean_square_error": self.root_mean_square_error,
            "r_squared": self.r_squared,
            "accuracy_percentage": self.accuracy_percentage,
            "evaluated_at": self.evaluated_at.isoformat(),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "predictions_evaluated": self.predictions_evaluated,
        }
