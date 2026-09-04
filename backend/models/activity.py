from sqlalchemy import Column, String, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"))
    
    # Action details
    action_type = Column(String(100))  # 'report_submitted', 'prediction_requested', etc
    details = Column(JSON)  # additional context
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="activity_logs")
    location = relationship("Location", back_populates="activity_logs")

    __table_args__ = (
        Index("idx_activity_user", "user_id"),
        Index("idx_activity_action", "action_type"),
        Index("idx_activity_created", "created_at"),
    )

    def __repr__(self):
        return f"<ActivityLog user_id={self.user_id} action={self.action_type}>"

    @staticmethod
    def log_action(session, user_id: str, action_type: str, location_id: str = None, details: dict = None):
        """Create an activity log entry."""
        log_entry = ActivityLog(
            user_id=uuid.UUID(user_id) if user_id else None,
            location_id=uuid.UUID(location_id) if location_id else None,
            action_type=action_type,
            details=details or {}
        )
        session.add(log_entry)
        return log_entry

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "location_id": str(self.location_id) if self.location_id else None,
            "action_type": self.action_type,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
        }
