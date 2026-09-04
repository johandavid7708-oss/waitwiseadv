"""
WaitWise ML Prediction Engine

This module implements the core prediction algorithm that:
1. Learns from historical crowd data
2. Predicts future crowd levels
3. Improves accuracy over time based on feedback
4. Detects anomalies and patterns
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Prediction, LearningPattern, CrowdReport, CrowdAggregate


@dataclass
class PredictionResult:
    """Result of a crowd prediction."""
    location_id: str
    predicted_crowd_level: float
    predicted_wait_time: int
    confidence_score: float
    reasoning: str
    model_version: str = "1.0"
    base_level: float = None
    trend_adjustment: float = None
    pattern_adjustment: float = None
    anomaly_score: float = None


class CrowdPredictionEngine:
    """
    Advanced ML-based crowd prediction engine.
    
    Algorithm:
    1. Get historical patterns for this day/hour
    2. Calculate base crowd level from patterns
    3. Apply real-time trend adjustments
    4. Detect anomalies and adjust confidence
    5. Return prediction with confidence score
    """
    
    def __init__(self, model_version: str = "1.0"):
        self.model_version = model_version
        self.anomaly_threshold = 2.5  # Standard deviations from mean
        
    def predict(self, 
                session: Session,
                location_id: str,
                forecast_minutes: int = 30) -> PredictionResult:
        """
        Predict crowd level for a location.
        
        Args:
            session: Database session
            location_id: UUID of location
            forecast_minutes: How many minutes ahead to predict (30, 60, 120, etc)
        
        Returns:
            PredictionResult with crowd level and confidence
        """
        
        # Calculate the target time
        forecast_time = datetime.utcnow() + timedelta(minutes=forecast_minutes)
        day_of_week = forecast_time.weekday()
        hour_of_day = forecast_time.hour
        
        # Get the learning pattern for this day/hour
        pattern = self._get_learning_pattern(
            session, location_id, day_of_week, hour_of_day
        )
        
        # Get base crowd level from pattern
        base_level = pattern.avg_crowd_level if pattern else 2.5  # default: medium crowd
        
        # Get recent reports to detect trends
        recent_reports = self._get_recent_reports(session, location_id, hours=2)
        trend_adjustment = self._calculate_trend(recent_reports)
        
        # Combine base level with trend
        predicted_level = self._apply_adjustments(
            base_level,
            trend_adjustment,
            pattern.std_dev_crowd if pattern else 0.8,
            forecast_time  # Pass the actual forecast time
        )
        
        # Detect if this is anomalous
        anomaly_score = self._detect_anomaly(
            predicted_level,
            recent_reports,
            pattern
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            pattern,
            anomaly_score,
            len(recent_reports)
        )
        
        # Estimate wait time
        wait_time = self._estimate_wait_time(predicted_level, location_id, session)
        
        return PredictionResult(
            location_id=location_id,
            predicted_crowd_level=max(1, min(5, predicted_level)),  # Clamp 1-5
            predicted_wait_time=wait_time,
            confidence_score=confidence,
            reasoning=self._generate_reasoning(base_level, trend_adjustment, pattern, anomaly_score),
            model_version=self.model_version,
            base_level=base_level,
            trend_adjustment=trend_adjustment,
            pattern_adjustment=pattern.avg_crowd_level if pattern else None,
            anomaly_score=anomaly_score
        )
    
    def _get_learning_pattern(self, 
                             session: Session, 
                             location_id: str,
                             day_of_week: int,
                             hour_of_day: int) -> Optional[LearningPattern]:
        """Retrieve learned pattern for this day/hour."""
        from sqlalchemy.dialects.postgresql import UUID
        import uuid
        
        try:
            location_uuid = uuid.UUID(location_id)
        except:
            location_uuid = location_id
        
        pattern = session.query(LearningPattern).filter(
            LearningPattern.location_id == location_uuid,
            LearningPattern.day_of_week == day_of_week,
            LearningPattern.hour_of_day == hour_of_day
        ).first()
        
        return pattern
    
    def _get_recent_reports(self, 
                           session: Session, 
                           location_id: str,
                           hours: int = 2) -> List[CrowdReport]:
        """Get recent crowd reports for trend analysis."""
        from sqlalchemy.dialects.postgresql import UUID
        import uuid
        
        try:
            location_uuid = uuid.UUID(location_id)
        except:
            location_uuid = location_id
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        reports = session.query(CrowdReport).filter(
            CrowdReport.location_id == location_uuid,
            CrowdReport.created_at >= cutoff,
            CrowdReport.is_verified == True  # Only trust verified reports
        ).order_by(CrowdReport.created_at.desc()).all()
        
        return reports
    
    def _calculate_trend(self, recent_reports: List[CrowdReport]) -> float:
        """
        Calculate trend in crowd levels.
        
        Returns:
            Adjustment factor (-1.0 to +1.0)
            Positive = getting more crowded
            Negative = getting less crowded
        """
        if len(recent_reports) < 2:
            return 0.0
        
        # Get crowd levels in chronological order
        levels = [r.crowd_level for r in reversed(recent_reports)]
        
        # Calculate trend using simple linear regression
        x = np.arange(len(levels))
        y = np.array(levels)
        
        # Fit line: trend = (y2 - y1) / len
        trend_direction = (levels[-1] - levels[0]) / len(levels)
        
        # Normalize to -1 to +1 range
        trend = np.clip(trend_direction, -1, 1)
        
        return float(trend)
    
    def _apply_adjustments(self, 
                          base_level: float,
                          trend: float,
                          std_dev: float,
                          forecast_time: datetime = None) -> float:
        """
        Apply trend and contextual adjustments to base level.
        
        Formula:
        adjusted = base + (trend * trend_weight) + (time_of_day_adjustment)
        """
        
        # Use forecast time if provided, otherwise current time
        if forecast_time is None:
            forecast_time = datetime.utcnow()
        
        hour = forecast_time.hour
        
        # Time-based adjustment
        # Assume peaks between 18-21 and 12-14
        time_adjustment = 0.0
        if 18 <= hour <= 21 or 12 <= hour <= 14:
            time_adjustment = 0.3  # Expect 15% higher during peak hours
        elif 6 <= hour <= 9 or 22 <= hour <= 23:
            time_adjustment = -0.2  # Expect lower in morning/late night
        
        # Combine adjustments
        adjusted = base_level + (trend * 0.6) + time_adjustment
        
        return adjusted
    
    def _detect_anomaly(self,
                       predicted_level: float,
                       recent_reports: List[CrowdReport],
                       pattern: Optional[LearningPattern]) -> float:
        """
        Detect if predicted level is anomalous.
        
        Returns:
            Anomaly score (0-1, where 1 is completely anomalous)
        """
        
        if not recent_reports or not pattern:
            return 0.0
        
        recent_levels = [r.crowd_level for r in recent_reports]
        
        # Calculate z-score
        mean = statistics.mean(recent_levels)
        std = statistics.stdev(recent_levels) if len(recent_levels) > 1 else 1.0
        
        if std == 0:
            return 0.0
        
        z_score = abs((predicted_level - mean) / std)
        
        # Convert to 0-1 anomaly score
        anomaly_score = min(1.0, z_score / self.anomaly_threshold)
        
        return anomaly_score
    
    def _calculate_confidence(self,
                             pattern: Optional[LearningPattern],
                             anomaly_score: float,
                             recent_report_count: int) -> float:
        """
        Calculate confidence in prediction.
        
        Factors:
        - Pattern confidence (more historical data = higher confidence)
        - Anomaly (anomalies reduce confidence)
        - Recent reports (more recent data = higher confidence)
        """
        
        base_confidence = 0.5
        
        # Pattern confidence (0.3 to 0.9)
        if pattern:
            pattern_confidence = min(0.9, 0.3 + (pattern.confidence or 0.5) * 0.6)
        else:
            pattern_confidence = 0.3
        
        # Recent data boost (0.1 to 0.2 additional)
        recent_boost = min(0.2, recent_report_count * 0.05)
        
        # Anomaly penalty (0 to -0.3)
        anomaly_penalty = -anomaly_score * 0.3
        
        confidence = pattern_confidence + recent_boost + anomaly_penalty
        
        return np.clip(float(confidence), 0.3, 0.99)
    
    def _estimate_wait_time(self,
                           crowd_level: float,
                           location_id: str,
                           session: Session) -> int:
        """
        Estimate wait time based on crowd level.
        
        Empirical formula:
        wait_time = 2 + (crowd_level ^ 2) * 8
        """
        
        # Get average wait times from recent reports for this location
        from sqlalchemy.dialects.postgresql import UUID
        import uuid
        
        try:
            location_uuid = uuid.UUID(location_id)
        except:
            location_uuid = location_id
        
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        avg_wait = session.query(
            func.avg(CrowdReport.wait_time_minutes)
        ).filter(
            CrowdReport.location_id == location_uuid,
            CrowdReport.wait_time_minutes.isnot(None),
            CrowdReport.created_at >= cutoff
        ).scalar()
        
        if avg_wait:
            # Scale by crowd level ratio
            baseline_crowd = 3.0  # Medium
            ratio = crowd_level / baseline_crowd
            wait_time = int(avg_wait * ratio)
        else:
            # Default formula
            wait_time = int(2 + (crowd_level ** 2) * 8)
        
        return max(1, min(120, wait_time))  # Clamp 1-120 minutes
    
    def _generate_reasoning(self,
                           base_level: float,
                           trend: float,
                           pattern: Optional[LearningPattern],
                           anomaly_score: float) -> str:
        """Generate human-readable explanation of prediction."""
        
        reasons = []
        
        # Base level reasoning
        if base_level > 3.5:
            reasons.append("Historical data shows this is typically very crowded")
        elif base_level > 2.5:
            reasons.append("Historical data shows moderate crowd levels")
        else:
            reasons.append("Historical data shows this is usually quiet")
        
        # Trend reasoning
        if trend > 0.3:
            reasons.append("Current trend is getting more crowded")
        elif trend < -0.3:
            reasons.append("Current trend is getting less crowded")
        
        # Anomaly reasoning
        if anomaly_score > 0.7:
            reasons.append("⚠️ Unusual activity detected - confidence reduced")
        
        return " • ".join(reasons) if reasons else "Standard prediction"


def create_prediction_db_entry(session: Session,
                               location_id: str,
                               result: PredictionResult) -> Prediction:
    """Create a Prediction database record from PredictionResult."""
    from sqlalchemy.dialects.postgresql import UUID
    import uuid
    
    try:
        location_uuid = uuid.UUID(location_id)
    except:
        location_uuid = location_id
    
    forecast_time = datetime.utcnow() + timedelta(
        minutes=result.model_version.split('.')[-1]  # Extract minutes from version (hack for demo)
    )
    
    prediction = Prediction(
        location_id=location_uuid,
        predicted_crowd_level=result.predicted_crowd_level,
        predicted_wait_time=result.predicted_wait_time,
        confidence_score=result.confidence_score,
        prediction_horizon=30,
        model_version=result.model_version,
        predicted_at=datetime.utcnow(),
        forecast_for=forecast_time
    )
    
    session.add(prediction)
    return prediction
