from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
import uuid

from .base import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # shopping_mall, restaurant, park, hospital, store
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    geom = Column(Geometry("POINT", srid=4326))
    
    capacity = Column(Integer)
    typical_peak_start = Column(Integer, default=18)  # hour of day
    typical_peak_end = Column(Integer, default=21)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    crowd_reports = relationship("CrowdReport", back_populates="location", cascade="all, delete-orphan")
    crowd_aggregates = relationship("CrowdAggregate", back_populates="location", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="location", cascade="all, delete-orphan")
    learning_patterns = relationship("LearningPattern", back_populates="location", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="current_location", foreign_keys="Recommendation.current_location_id")
    alerts = relationship("Alert", back_populates="location", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="location", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_locations_category", "category"),
        Index("idx_locations_active", "is_active"),
    )

    def __repr__(self):
        return f"<Location {self.name} ({self.category})>"

    def get_current_crowd_level(self, session):
        """Get the most recent crowd level for this location."""
        from .crowd import CrowdReport
        
        latest_report = session.query(CrowdReport).filter(
            CrowdReport.location_id == self.id
        ).order_by(CrowdReport.created_at.desc()).first()
        
        return latest_report.crowd_level if latest_report else None

    def get_hourly_aggregate(self, session, hours_back=1):
        """Get crowd aggregate for the past N hours."""
        from sqlalchemy import func
        from .crowd import CrowdReport
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        
        result = session.query(
            func.avg(CrowdReport.crowd_level).label("avg_crowd"),
            func.max(CrowdReport.crowd_level).label("max_crowd"),
            func.count(CrowdReport.id).label("report_count")
        ).filter(
            CrowdReport.location_id == self.id,
            CrowdReport.created_at >= cutoff
        ).first()
        
        return {
            "avg_crowd_level": float(result.avg_crowd) if result.avg_crowd else None,
            "max_crowd_level": result.max_crowd,
            "report_count": result.report_count,
        }

    def distance_to(self, other_location):
        """Calculate distance to another location in km."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [self.longitude, self.latitude, other_location.longitude, other_location.latitude])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km

    def to_dict(self, include_current_crowd=False, session=None):
        """Convert to dictionary."""
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "capacity": self.capacity,
            "typical_peak_start": self.typical_peak_start,
            "typical_peak_end": self.typical_peak_end,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_current_crowd and session:
            data["current_crowd_level"] = self.get_current_crowd_level(session)
            data["hourly_data"] = self.get_hourly_aggregate(session)
        
        return data
