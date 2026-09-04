from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"))
    
    # Alert configuration
    alert_type = Column(String(50), nullable=False)  # 'crowd_spike', 'peak_starting', 'less_crowded_alternative'
    trigger_condition = Column(JSON)  # stores the condition that triggered
    
    # Status
    is_active = Column(Boolean, default=True)
    was_sent = Column(Boolean, default=False)
    
    # Notification details
    title = Column(String(255))
    message = Column(Text)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")
    location = relationship("Location", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_user", "user_id"),
        Index("idx_alerts_active", "is_active"),
    )

    def __repr__(self):
        return f"<Alert user_id={self.user_id} type={self.alert_type}>"

    def mark_sent(self):
        """Mark alert as sent."""
        self.was_sent = True
        self.sent_at = datetime.utcnow()

    def deactivate(self):
        """Deactivate alert."""
        self.is_active = False

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "location_id": str(self.location_id) if self.location_id else None,
            "alert_type": self.alert_type,
            "trigger_condition": self.trigger_condition,
            "is_active": self.is_active,
            "was_sent": self.was_sent,
            "title": self.title,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
