from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class CrowdReport(Base):
    __tablename__ = "crowd_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    
    crowd_level = Column(Integer, nullable=False)  # 1-5 scale
    wait_time_minutes = Column(Integer)
    confidence = Column(Float, default=0.5)  # 0-1
    comment = Column(Text)
    photo_url = Column(String(500))
    
    accuracy_votes = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.5)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    location = relationship("Location", back_populates="crowd_reports")
    user = relationship("User", back_populates="crowd_reports")

    __table_args__ = (
        Index("idx_reports_location", "location_id"),
        Index("idx_reports_user", "user_id"),
        Index("idx_reports_created", "created_at"),
        Index("idx_reports_verified", "is_verified"),
    )

    def __repr__(self):
        return f"<CrowdReport location_id={self.location_id} level={self.crowd_level}>"

    def upvote_accuracy(self):
        """Increase accuracy votes."""
        self.accuracy_votes += 1
        # Update accuracy score based on votes
        self.accuracy_score = min(1.0, 0.5 + (self.accuracy_votes * 0.05))

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "location_id": str(self.location_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "crowd_level": self.crowd_level,
            "wait_time_minutes": self.wait_time_minutes,
            "confidence": self.confidence,
            "comment": self.comment,
            "photo_url": self.photo_url,
            "accuracy_votes": self.accuracy_votes,
            "accuracy_score": self.accuracy_score,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CrowdAggregate(Base):
    __tablename__ = "crowd_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    
    hour_timestamp = Column(DateTime, nullable=False)
    avg_crowd_level = Column(Float)
    max_crowd_level = Column(Integer)
    min_crowd_level = Column(Integer)
    avg_wait_time = Column(Integer)
    report_count = Column(Integer)
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    location = relationship("Location", back_populates="crowd_aggregates")

    __table_args__ = (
        Index("idx_aggregates_location_time", "location_id", "hour_timestamp"),
    )

    def __repr__(self):
        return f"<CrowdAggregate location_id={self.location_id} hour={self.hour_timestamp}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "location_id": str(self.location_id),
            "hour_timestamp": self.hour_timestamp.isoformat(),
            "avg_crowd_level": self.avg_crowd_level,
            "max_crowd_level": self.max_crowd_level,
            "min_crowd_level": self.min_crowd_level,
            "avg_wait_time": self.avg_wait_time,
            "report_count": self.report_count,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }
