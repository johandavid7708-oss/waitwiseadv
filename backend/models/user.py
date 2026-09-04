from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255))
    
    is_trusted_reporter = Column(Boolean, default=False)
    reputation_score = Column(Integer, default=0)
    preferences = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    preferences_rel = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    crowd_reports = relationship("CrowdReport", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("UserFeedback", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_trusted", "is_trusted_reporter"),
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def is_password_correct(self, password: str) -> bool:
        """Verify password (implement with bcrypt in production)."""
        # In production, use: bcrypt.checkpw(password.encode(), self.password_hash)
        # For demo: simple comparison
        return password == self.password_hash  # NOT SECURE - for demo only

    def increase_reputation(self, points: int = 1):
        """Increase user reputation score."""
        self.reputation_score += points
        if self.reputation_score >= 10:
            self.is_trusted_reporter = True

    def get_report_accuracy(self, session):
        """Get this user's report accuracy percentage."""
        from sqlalchemy import func
        from .crowd import CrowdReport
        
        total = session.query(func.count(CrowdReport.id)).filter(
            CrowdReport.user_id == self.id
        ).scalar()
        
        if total == 0:
            return 0
        
        accurate = session.query(func.count(CrowdReport.id)).filter(
            CrowdReport.user_id == self.id,
            CrowdReport.is_verified == True
        ).scalar()
        
        return (accurate / total) * 100

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "is_trusted_reporter": self.is_trusted_reporter,
            "reputation_score": self.reputation_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    preferred_categories = Column(ARRAY(String), default=[])
    avoid_crowded = Column(Boolean, default=False)
    prefer_quiet = Column(Boolean, default=False)
    max_wait_tolerance = Column(Integer, default=30)  # minutes
    travel_preferences = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences_rel")

    __table_args__ = (
        Index("idx_user_prefs_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<UserPreferences user_id={self.user_id}>"

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "preferred_categories": self.preferred_categories,
            "avoid_crowded": self.avoid_crowded,
            "prefer_quiet": self.prefer_quiet,
            "max_wait_tolerance": self.max_wait_tolerance,
            "travel_preferences": self.travel_preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
