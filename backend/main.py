"""
WaitWise v2.0 Backend

A predictive human-flow intelligence platform that learns and improves over time.

Features:
- Real-time crowd tracking
- ML-based predictions with self-learning
- Smart recommendations
- User notifications and alerts
- Comprehensive analytics
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Depends, WebSocket, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import uvicorn

# Import models
from models import (
    Base,
    Location,
    User,
    UserPreferences,
    CrowdReport,
    Prediction,
    Recommendation,
    Alert,
    UserFeedback,
    ActivityLog,
)

# Import ML systems
from ml import CrowdPredictionEngine, SelfLearningSystem, run_learning_cycle

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/waitwise")
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"

# For production with PostgreSQL
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        echo=SQLALCHEMY_ECHO,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
else:
    # Fallback to SQLite for development
    engine = create_engine(
        "sqlite:///./waitwise.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=SQLALCHEMY_ECHO
    )

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CrowdReportRequest(BaseModel):
    """Request body for submitting a crowd report."""
    location_id: str
    crowd_level: int
    wait_time_minutes: Optional[int] = None
    comment: Optional[str] = None
    confidence: float = 0.5


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="WaitWise v2.0",
    description="Predictive human-flow intelligence platform",
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# INITIALIZATION
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and background tasks."""
    logger.info("Starting WaitWise Backend v2.0")
    
    # Create all tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
    
    # Seed sample data if needed
    with get_db_context() as db:
        location_count = db.query(Location).count()
        if location_count == 0:
            logger.info("Seeding sample locations...")
            _seed_sample_data(db)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down WaitWise Backend")


def _seed_sample_data(db: Session):
    """Seed database with sample data."""
    locations = [
        Location(
            name="Central Mall",
            description="Major shopping center",
            category="shopping_mall",
            latitude=40.7128,
            longitude=-74.0060,
            capacity=5000,
            typical_peak_start=18,
            typical_peak_end=21
        ),
        Location(
            name="Burger House",
            description="Popular burger restaurant",
            category="restaurant",
            latitude=40.7150,
            longitude=-74.0050,
            capacity=200,
            typical_peak_start=12,
            typical_peak_end=14
        ),
        Location(
            name="Tech Store",
            description="Electronics retail shop",
            category="store",
            latitude=40.7180,
            longitude=-74.0080,
            capacity=300,
            typical_peak_start=15,
            typical_peak_end=19
        ),
        Location(
            name="City Park",
            description="Large urban park",
            category="park",
            latitude=40.7200,
            longitude=-74.0100,
            capacity=10000,
            typical_peak_start=10,
            typical_peak_end=18
        ),
    ]
    
    db.add_all(locations)
    db.commit()
    logger.info(f"Seeded {len(locations)} sample locations")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """Check backend health."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        
        # Get stats
        location_count = db.query(Location).count()
        report_count = db.query(CrowdReport).count()
        prediction_count = db.query(Prediction).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "stats": {
                "locations": location_count,
                "reports": report_count,
                "predictions": prediction_count
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


# ============================================================================
# LOCATIONS ENDPOINTS
# ============================================================================

@app.get("/api/v1/locations", tags=["Locations"])
async def get_locations(
    category: Optional[str] = None,
    active_only: bool = True,
    include_crowd: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all locations with optional filtering.
    
    Query Parameters:
    - category: Filter by category (shopping_mall, restaurant, park, etc)
    - active_only: Only return active locations
    - include_crowd: Include current crowd level data
    """
    query = db.query(Location)
    
    if active_only:
        query = query.filter(Location.is_active == True)
    
    if category:
        query = query.filter(Location.category == category)
    
    locations = query.all()
    
    result = []
    for location in locations:
        data = location.to_dict(include_current_crowd=include_crowd, session=db)
        result.append(data)
    
    return {"locations": result, "count": len(result)}


@app.get("/api/v1/locations/{location_id}", tags=["Locations"])
async def get_location(location_id: str, db: Session = Depends(get_db)):
    """Get a specific location with detailed information."""
    try:
        import uuid
        location = db.query(Location).filter(Location.id == uuid.UUID(location_id)).first()
    except:
        location = None
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Get detailed stats
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_reports = db.query(CrowdReport).filter(
        CrowdReport.location_id == location.id,
        CrowdReport.created_at >= seven_days_ago,
        CrowdReport.is_verified == True
    ).all()
    
    avg_crowd = (sum(r.crowd_level for r in recent_reports) / len(recent_reports)) if recent_reports else None
    
    return {
        **location.to_dict(include_current_crowd=True, session=db),
        "stats": {
            "recent_reports": len(recent_reports),
            "avg_crowd_7days": avg_crowd,
            "distance_category": "nearby"
        }
    }


# ============================================================================
# CROWD REPORTS ENDPOINTS
# ============================================================================

@app.post("/api/v1/reports", tags=["Reports"])
async def submit_crowd_report(
    report: CrowdReportRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a crowd report for a location.
    
    Request Body:
    {
        "location_id": "uuid-string",
        "crowd_level": 3,
        "wait_time_minutes": 15,
        "comment": "Getting busy",
        "confidence": 0.8
    }
    """
    
    # Validate crowd level
    if not (1 <= report.crowd_level <= 5):
        raise HTTPException(status_code=400, detail="Crowd level must be between 1 and 5")
    
    # Validate confidence
    if not (0 <= report.confidence <= 1):
        raise HTTPException(status_code=400, detail="Confidence must be between 0 and 1")
    
    # Check location exists
    try:
        import uuid
        location = db.query(Location).filter(Location.id == uuid.UUID(report.location_id)).first()
    except:
        location = None
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Create report
    crowd_report = CrowdReport(
        location_id=location.id,
        crowd_level=report.crowd_level,
        wait_time_minutes=report.wait_time_minutes,
        comment=report.comment,
        confidence=report.confidence,
        accuracy_score=0.5  # Initial score
    )
    
    db.add(crowd_report)
    db.commit()
    db.refresh(crowd_report)
    
    logger.info(f"Report created for {location.name}: crowd_level={report.crowd_level}")
    
    return {
        "status": "success",
        "report_id": str(crowd_report.id),
        "created_at": crowd_report.created_at.isoformat(),
        "location_id": str(location.id),
        "location_name": location.name
    }


@app.get("/api/v1/reports/{location_id}", tags=["Reports"])
async def get_location_reports(
    location_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get recent reports for a location."""
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    try:
        import uuid
        reports = db.query(CrowdReport).filter(
            CrowdReport.location_id == uuid.UUID(location_id),
            CrowdReport.created_at >= cutoff
        ).order_by(CrowdReport.created_at.desc()).all()
    except:
        reports = []
    
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    
    return {
        "location_id": location_id,
        "reports": [r.to_dict() for r in reports],
        "count": len(reports),
        "timeframe_hours": hours
    }


@app.post("/api/v1/reports/{report_id}/verify", tags=["Reports"])
async def verify_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Verify a crowd report as accurate.
    
    Once verified, the report contributes to the learning system.
    This enables predictions and learning patterns to improve.
    """
    try:
        import uuid
        report = db.query(CrowdReport).filter(
            CrowdReport.id == uuid.UUID(report_id)
        ).first()
    except:
        report = None
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.is_verified:
        return {
            "status": "already_verified",
            "report_id": str(report.id),
            "message": "Report was already verified"
        }
    
    # Mark as verified
    report.is_verified = True
    report.accuracy_score = 0.8  # Boost accuracy for verified reports
    db.commit()
    
    logger.info(f"Report {report_id} verified for location {report.location_id}")
    
    return {
        "status": "success",
        "report_id": str(report.id),
        "verified_at": datetime.utcnow().isoformat(),
        "message": "Report verified. Contributes to AI learning."
    }


@app.post("/api/v1/reports/bulk-verify/{location_id}", tags=["Reports"])
async def verify_recent_reports(
    location_id: str,
    hours: int = Query(1, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """
    Verify all recent reports for a location (for testing/seeding).
    
    This is useful for bootstrap testing. In production, you'd use
    a proper trust system or manual verification.
    """
    
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    try:
        import uuid
        reports = db.query(CrowdReport).filter(
            CrowdReport.location_id == uuid.UUID(location_id),
            CrowdReport.created_at >= cutoff,
            CrowdReport.is_verified == False
        ).all()
    except:
        reports = []
    
    if not reports:
        return {
            "status": "no_reports",
            "verified_count": 0,
            "message": "No unverified reports found"
        }
    
    # Verify all
    for report in reports:
        report.is_verified = True
        report.accuracy_score = 0.75
    
    db.commit()
    
    logger.info(f"Verified {len(reports)} reports for location {location_id}")
    
    return {
        "status": "success",
        "verified_count": len(reports),
        "location_id": location_id,
        "message": f"Verified {len(reports)} reports"
    }


# ============================================================================
# PREDICTIONS ENDPOINTS
# ============================================================================

@app.get("/api/v1/predictions/{location_id}", tags=["Predictions"])
async def get_prediction(
    location_id: str,
    minutes_ahead: int = Query(30, ge=15, le=240),
    db: Session = Depends(get_db)
):
    """
    Get a real-time crowd prediction for a location.
    
    Uses ML engine trained on historical data and current trends.
    """
    
    try:
        import uuid
        location = db.query(Location).filter(Location.id == uuid.UUID(location_id)).first()
    except:
        location = None
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Generate prediction using ML engine
    engine = CrowdPredictionEngine(model_version="1.0")
    prediction_result = engine.predict(db, location_id, minutes_ahead)
    
    # Save to database
    forecast_time = datetime.utcnow() + timedelta(minutes=minutes_ahead)
    
    prediction = Prediction(
        location_id=location.id,
        predicted_crowd_level=prediction_result.predicted_crowd_level,
        predicted_wait_time=prediction_result.predicted_wait_time,
        confidence_score=prediction_result.confidence_score,
        prediction_horizon=minutes_ahead,
        model_version="1.0",
        predicted_at=datetime.utcnow(),
        forecast_for=forecast_time
    )
    
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return {
        "location_id": location_id,
        "location_name": location.name,
        "prediction": {
            "predicted_crowd_level": prediction_result.predicted_crowd_level,
            "crowd_level_text": _crowd_level_to_text(prediction_result.predicted_crowd_level),
            "predicted_wait_time": prediction_result.predicted_wait_time,
            "confidence_score": prediction_result.confidence_score,
            "prediction_horizon_minutes": minutes_ahead,
            "reasoning": prediction_result.reasoning,
        },
        "forecast_for": forecast_time.isoformat(),
        "generated_at": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/forecast/{location_id}", tags=["Predictions"])
async def get_24hour_forecast(location_id: str, db: Session = Depends(get_db)):
    """
    Get a 24-hour crowd forecast for a location.
    
    Returns hourly predictions for the next 24 hours.
    """
    
    try:
        import uuid
        location = db.query(Location).filter(Location.id == uuid.UUID(location_id)).first()
    except:
        location = None
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    engine = CrowdPredictionEngine()
    
    forecast = []
    for hour in range(24):
        minutes_ahead = (hour + 1) * 60
        
        prediction_result = engine.predict(db, location_id, minutes_ahead)
        forecast_time = datetime.utcnow() + timedelta(minutes=minutes_ahead)
        
        forecast.append({
            "hour": hour,
            "time": forecast_time.isoformat(),
            "predicted_crowd_level": prediction_result.predicted_crowd_level,
            "predicted_wait_time": prediction_result.predicted_wait_time,
            "confidence_score": prediction_result.confidence_score,
        })
    
    return {
        "location_id": location_id,
        "location_name": location.name,
        "forecast": forecast,
        "generated_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# RECOMMENDATIONS ENDPOINTS
# ============================================================================

@app.post("/api/v1/recommendations", tags=["Recommendations"])
async def get_recommendations(
    location_id: str,
    max_distance_km: float = 2.0,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get smart alternative location recommendations.
    
    Returns locations with lower expected wait times and better crowd conditions.
    """
    
    try:
        import uuid
        current_location = db.query(Location).filter(
            Location.id == uuid.UUID(location_id)
        ).first()
    except:
        current_location = None
    
    if not current_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Get all other locations
    other_locations = db.query(Location).filter(
        Location.id != current_location.id,
        Location.is_active == True
    ).all()
    
    # Score each alternative
    engine = CrowdPredictionEngine()
    recommendations = []
    
    for alt_location in other_locations:
        distance = current_location.distance_to(alt_location)
        
        if distance > max_distance_km:
            continue
        
        # Get predictions for both
        current_pred = engine.predict(db, current_location.id, 30)
        alt_pred = engine.predict(db, alt_location.id, 30)
        
        # Calculate savings
        wait_time_savings = current_pred.predicted_wait_time - alt_pred.predicted_wait_time
        
        if wait_time_savings > 0:
            rec = Recommendation(
                current_location_id=current_location.id,
                recommended_location_id=alt_location.id,
                wait_time_savings=int(wait_time_savings),
                distance_km=distance,
                travel_time_minutes=int(distance * 2),  # Assume 2 min per km
                recommendation_score=None  # Will calculate below
            )
            
            # Calculate score
            rec.calculate_score(wait_time_savings)
            rec.set_reason()
            
            recommendations.append(rec)
    
    # Sort by score and limit
    recommendations.sort(key=lambda r: r.recommendation_score or 0, reverse=True)
    recommendations = recommendations[:limit]
    
    return {
        "current_location_id": location_id,
        "current_location_name": current_location.name,
        "recommendations": [
            {
                "recommended_location_id": str(r.recommended_location_id),
                "recommended_location_name": db.query(Location).get(r.recommended_location_id).name,
                "reason": r.reason,
                "wait_time_savings": r.wait_time_savings,
                "distance_km": r.distance_km,
                "travel_time_minutes": r.travel_time_minutes,
                "recommendation_score": r.recommendation_score,
            }
            for r in recommendations
        ],
        "count": len(recommendations)
    }


# ============================================================================
# LEARNING ENDPOINTS
# ============================================================================

@app.post("/api/v1/learning/run-cycle", tags=["Learning"])
async def run_learning_cycle_endpoint(background_tasks: BackgroundTasks):
    """
    Trigger the self-learning cycle.
    
    This updates patterns from reports, verifies predictions, and improves the model.
    """
    
    def execute_learning():
        with get_db_context() as db:
            results = run_learning_cycle(db)
            logger.info(f"Learning cycle completed: {results['locations_processed']} locations processed")
    
    background_tasks.add_task(execute_learning)
    
    return {
        "status": "learning_cycle_queued",
        "message": "Learning cycle started in background",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/feedback", tags=["Learning"])
async def submit_feedback(
    prediction_id: str,
    feedback_type: str,
    rating: int,
    comment: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a prediction.
    
    Helps the system learn and improve accuracy.
    """
    
    try:
        import uuid
        prediction = db.query(Prediction).filter(
            Prediction.id == uuid.UUID(prediction_id)
        ).first()
    except:
        prediction = None
    
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    feedback = UserFeedback(
        prediction_id=prediction.id,
        feedback_type=feedback_type,
        rating=rating,
        comment=comment
    )
    
    db.add(feedback)
    db.commit()
    
    logger.info(f"Feedback submitted for prediction {prediction_id}: rating={rating}")
    
    return {
        "status": "success",
        "feedback_id": str(feedback.id),
        "message": "Thank you for helping us improve!"
    }


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/analytics/{location_id}", tags=["Analytics"])
async def get_location_analytics(
    location_id: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get analytics for a location.
    
    Includes crowd trends, peak times, prediction accuracy, etc.
    """
    
    try:
        import uuid
        location = db.query(Location).filter(Location.id == uuid.UUID(location_id)).first()
    except:
        location = None
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get reports
    reports = db.query(CrowdReport).filter(
        CrowdReport.location_id == location.id,
        CrowdReport.created_at >= cutoff,
        CrowdReport.is_verified == True
    ).all()
    
    if not reports:
        return {
            "location_id": location_id,
            "analytics": {
                "report_count": 0,
                "message": "No data available"
            }
        }
    
    crowd_levels = [r.crowd_level for r in reports]
    wait_times = [r.wait_time_minutes for r in reports if r.wait_time_minutes]
    
    return {
        "location_id": location_id,
        "location_name": location.name,
        "analytics": {
            "period_days": days,
            "report_count": len(reports),
            "avg_crowd_level": sum(crowd_levels) / len(crowd_levels),
            "max_crowd_level": max(crowd_levels),
            "min_crowd_level": min(crowd_levels),
            "avg_wait_time": sum(wait_times) // len(wait_times) if wait_times else None,
            "peak_hour": _find_peak_hour(reports),
            "least_busy_hour": _find_least_busy_hour(reports),
        }
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _crowd_level_to_text(level: float) -> str:
    """Convert numeric crowd level to text."""
    if level < 1.5:
        return "Empty"
    elif level < 2.5:
        return "Quiet"
    elif level < 3.5:
        return "Moderate"
    elif level < 4.5:
        return "Crowded"
    else:
        return "Very Crowded"


def _find_peak_hour(reports: List[CrowdReport]) -> Optional[int]:
    """Find the peak hour from reports."""
    if not reports:
        return None
    
    hour_counts = {}
    for report in reports:
        hour = report.created_at.hour
        if hour not in hour_counts:
            hour_counts[hour] = []
        hour_counts[hour].append(report.crowd_level)
    
    if not hour_counts:
        return None
    
    peak_hour = max(hour_counts, key=lambda h: sum(hour_counts[h]) / len(hour_counts[h]))
    return peak_hour


def _find_least_busy_hour(reports: List[CrowdReport]) -> Optional[int]:
    """Find the least busy hour from reports."""
    if not reports:
        return None
    
    hour_counts = {}
    for report in reports:
        hour = report.created_at.hour
        if hour not in hour_counts:
            hour_counts[hour] = []
        hour_counts[hour].append(report.crowd_level)
    
    if not hour_counts:
        return None
    
    least_busy = min(hour_counts, key=lambda h: sum(hour_counts[h]) / len(hour_counts[h]))
    return least_busy


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENV") != "production",
        log_level="info"
    )
