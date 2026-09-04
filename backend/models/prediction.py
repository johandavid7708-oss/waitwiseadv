from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    
    # Prediction details
    predicted_crowd_level = Column(Float)
    predicted_wait_time = Column(Integer)
    confidence_score = Column(Float)
    prediction_horizon = Column(Integer)  # minutes ahead
    
    # Accuracy tracking
    actual_crowd_level = Column(Float)
    actual_wait_time = Column(Integer)
    accuracy_error = Column(Float)
    
    # Model info
    model_version = Column(String(50))
    
    predicted_at = Column(DateTime, nullable=False)
    forecast_for = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("Location", back_populates="predictions")
    feedback = relationship("UserFeedback", back_populates="prediction")

    __table_args__ = (
        Index("idx_predictions_location_forecast", "location_id", "forecast_for"),
        Index("idx_predictions_verified", "verified_at"),
    )

    def __repr__(self):
        return f"<Prediction location_id={self.location_id} for={self.forecast_for}>"

    def calculate_accuracy(self):
        """Calculate accuracy error percentage."""
        if self.actual_crowd_level is None:
            return None
        
        if self.predicted_crowd_level is None:
            return None
        
        error = abs(self.predicted_crowd_level - self.actual_crowd_level)
        self.accuracy_error = (error / 5.0) * 100  # 5 is max crowd level
        return self.accuracy_error

    def is_accurate(self, tolerance=0.5):
        """Check if prediction is within tolerance."""
        if self.actual_crowd_level is None:
            return None
        
        error = abs(self.predicted_crowd_level - self.actual_crowd_level)
        return error <= tolerance

    def to_dict(self, include_actual=False):
        """Convert to dictionary."""
        data = {
            "id": str(self.id),
            "location_id": str(self.location_id),
            "predicted_crowd_level": self.predicted_crowd_level,
            "predicted_wait_time": self.predicted_wait_time,
            "confidence_score": self.confidence_score,
            "prediction_horizon": self.prediction_horizon,
            "model_version": self.model_version,
            "predicted_at": self.predicted_at.isoformat(),
            "forecast_for": self.forecast_for.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
        
        if include_actual:
            data.update({
                "actual_crowd_level": self.actual_crowd_level,
                "actual_wait_time": self.actual_wait_time,
                "accuracy_error": self.accuracy_error,
                "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            })
        
        return data


class LearningPattern(Base):
    __tablename__ = "learning_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    
    # Time dimensions
    day_of_week = Column(Integer)  # 0-6
    hour_of_day = Column(Integer)  # 0-23
    
    # Aggregated statistics
    avg_crowd_level = Column(Float)
    std_dev_crowd = Column(Float)
    avg_wait_time = Column(Integer)
    peak_probability = Column(Float)
    
    # Contextual factors
    weather_condition = Column(String(50))
    temperature_range = Column(String(50))
    has_events = Column(Boolean, default=False)
    is_holiday = Column(Boolean, default=False)
    is_weekend = Column(Boolean, default=False)
    
    # Training metadata
    sample_count = Column(Integer, default=0)
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("Location", back_populates="learning_patterns")

    __table_args__ = (
        Index("idx_patterns_location_time", "location_id", "day_of_week", "hour_of_day"),
    )

    def __repr__(self):
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"<LearningPattern location_id={self.location_id} {day_names[self.day_of_week]} {self.hour_of_day}:00>"

    def is_peak_hour(self, threshold=0.7):
        """Check if this pattern represents a peak hour."""
        return self.peak_probability >= threshold if self.peak_probability else False

    def update_from_reports(self, crowd_levels, wait_times):
        """Update pattern statistics from actual reports."""
        import statistics
        
        if not crowd_levels:
            return
        
        self.avg_crowd_level = statistics.mean(crowd_levels)
        self.std_dev_crowd = statistics.stdev(crowd_levels) if len(crowd_levels) > 1 else 0
        
        if wait_times:
            self.avg_wait_time = int(statistics.mean(wait_times))
        
        self.sample_count = len(crowd_levels)
        self.confidence = min(1.0, self.sample_count / 30)  # Confidence increases with samples

    def to_dict(self):
        """Convert to dictionary."""
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "id": str(self.id),
            "location_id": str(self.location_id),
            "day_of_week": self.day_of_week,
            "day_name": day_names[self.day_of_week] if self.day_of_week is not None else None,
            "hour_of_day": self.hour_of_day,
            "avg_crowd_level": self.avg_crowd_level,
            "std_dev_crowd": self.std_dev_crowd,
            "avg_wait_time": self.avg_wait_time,
            "peak_probability": self.peak_probability,
            "is_peak_hour": self.is_peak_hour(),
            "weather_condition": self.weather_condition,
            "temperature_range": self.temperature_range,
            "has_events": self.has_events,
            "is_holiday": self.is_holiday,
            "is_weekend": self.is_weekend,
            "sample_count": self.sample_count,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
