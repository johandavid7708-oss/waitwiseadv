"""
WaitWise Self-Learning System

Continuously learns from:
1. User feedback on predictions
2. Actual vs predicted crowd levels
3. New reports and patterns
4. Model performance metrics

Improves over time through:
1. Updating learning patterns with new data
2. Adjusting model weights based on accuracy
3. Detecting and adapting to new patterns
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    Prediction, 
    LearningPattern, 
    CrowdReport, 
    CrowdAggregate,
    UserFeedback,
    ModelPerformance
)


class SelfLearningSystem:
    """
    Autonomous learning system that improves prediction accuracy.
    
    Process:
    1. Collect verified crowd data
    2. Update historical patterns
    3. Calculate prediction errors
    4. Adjust model weights
    5. Track performance metrics
    """
    
    def __init__(self):
        self.learning_rate = 0.1  # How quickly to adapt to new data
        self.min_samples_for_update = 5  # Minimum samples to consider a pattern valid
        
    def learn_from_reports(self, session: Session, location_id: str) -> Dict:
        """
        Learn from recent crowd reports.
        
        This is called periodically to:
        1. Aggregate hourly reports
        2. Update learning patterns
        3. Calculate pattern confidence
        """
        
        # Get all reports from the past 48 hours
        cutoff = datetime.utcnow() - timedelta(hours=48)
        
        reports = session.query(CrowdReport).filter(
            CrowdReport.location_id == location_id,
            CrowdReport.created_at >= cutoff,
            CrowdReport.is_verified == True
        ).all()
        
        if not reports:
            return {"status": "no_data", "reports_processed": 0}
        
        # Group reports by hour and day of week
        grouped = self._group_reports_by_time(reports)
        
        # Update learning patterns
        updated_patterns = []
        for (day_of_week, hour_of_day), reports_group in grouped.items():
            pattern = self._update_learning_pattern(
                session, location_id, day_of_week, hour_of_day, reports_group
            )
            updated_patterns.append(pattern)
        
        return {
            "status": "success",
            "reports_processed": len(reports),
            "patterns_updated": len(updated_patterns),
            "location_id": location_id
        }
    
    def learn_from_predictions(self, session: Session, location_id: str) -> Dict:
        """
        Learn from prediction accuracy.
        
        This measures how accurate past predictions were and:
        1. Verifies predictions with actual data
        2. Calculates accuracy metrics
        3. Adjusts confidence scores
        4. Tracks model performance
        """
        
        # Get predictions from the past 48 hours that can now be verified
        cutoff_predicted = datetime.utcnow() - timedelta(hours=48)
        cutoff_verified = datetime.utcnow() - timedelta(hours=1)  # Give 1 hour buffer
        
        unverified_predictions = session.query(Prediction).filter(
            Prediction.location_id == location_id,
            Prediction.predicted_at >= cutoff_predicted,
            Prediction.forecast_for <= cutoff_verified,
            Prediction.verified_at.is_(None)
        ).all()
        
        verified_count = 0
        accuracy_errors = []
        
        for prediction in unverified_predictions:
            # Try to find actual crowd level from reports near forecast time
            actual_level = self._get_actual_crowd_level(
                session, location_id, prediction.forecast_for
            )
            
            if actual_level is not None:
                prediction.actual_crowd_level = actual_level
                prediction.calculate_accuracy()
                prediction.verified_at = datetime.utcnow()
                
                accuracy_errors.append(prediction.accuracy_error)
                verified_count += 1
        
        session.commit()
        
        # Calculate and log model performance
        if verified_count > 0:
            self._log_model_performance(
                session, location_id, accuracy_errors, verified_count
            )
        
        return {
            "status": "success",
            "predictions_verified": verified_count,
            "avg_error": statistics.mean(accuracy_errors) if accuracy_errors else None,
            "location_id": location_id
        }
    
    def learn_from_feedback(self, session: Session, location_id: str) -> Dict:
        """
        Learn from user feedback on predictions.
        
        User ratings improve:
        1. Model confidence scoring
        2. Report verification
        3. Alert triggering
        """
        
        # Get unprocessed feedback
        recent_feedback = session.query(UserFeedback).filter(
            UserFeedback.prediction_id.isnot(None)
        ).order_by(UserFeedback.created_at.desc()).limit(100).all()
        
        feedback_processed = 0
        
        for feedback in recent_feedback:
            if feedback.prediction and feedback.prediction.location_id == location_id:
                # Use user rating to adjust confidence
                if feedback.rating >= 4:
                    # User says prediction was accurate
                    feedback.prediction.confidence_score = min(1.0, feedback.prediction.confidence_score + 0.05)
                elif feedback.rating <= 2:
                    # User says prediction was inaccurate
                    feedback.prediction.confidence_score = max(0.2, feedback.prediction.confidence_score - 0.1)
                
                feedback_processed += 1
        
        if feedback_processed > 0:
            session.commit()
        
        return {
            "status": "success",
            "feedback_processed": feedback_processed,
            "location_id": location_id
        }
    
    def _group_reports_by_time(self, reports: List[CrowdReport]) -> Dict:
        """Group reports by (day_of_week, hour_of_day)."""
        grouped = {}
        
        for report in reports:
            day_of_week = report.created_at.weekday()
            hour_of_day = report.created_at.hour
            
            key = (day_of_week, hour_of_day)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(report)
        
        return grouped
    
    def _update_learning_pattern(self,
                                 session: Session,
                                 location_id: str,
                                 day_of_week: int,
                                 hour_of_day: int,
                                 reports: List[CrowdReport]) -> Optional[LearningPattern]:
        """
        Update a learning pattern with new data.
        
        This implements exponential moving average to gradually adapt
        """
        
        # Get or create pattern
        pattern = session.query(LearningPattern).filter(
            LearningPattern.location_id == location_id,
            LearningPattern.day_of_week == day_of_week,
            LearningPattern.hour_of_day == hour_of_day
        ).first()
        
        if not pattern:
            pattern = LearningPattern(
                location_id=location_id,
                day_of_week=day_of_week,
                hour_of_day=hour_of_day
            )
            session.add(pattern)
        
        # Calculate statistics from new reports
        crowd_levels = [r.crowd_level for r in reports]
        wait_times = [r.wait_time_minutes for r in reports if r.wait_time_minutes]
        
        if crowd_levels:
            new_avg_crowd = statistics.mean(crowd_levels)
            new_std_dev = statistics.stdev(crowd_levels) if len(crowd_levels) > 1 else 0
            
            # Apply learning rate (exponential moving average)
            if pattern.avg_crowd_level:
                pattern.avg_crowd_level = (
                    (1 - self.learning_rate) * pattern.avg_crowd_level +
                    self.learning_rate * new_avg_crowd
                )
                pattern.std_dev_crowd = (
                    (1 - self.learning_rate) * pattern.std_dev_crowd +
                    self.learning_rate * new_std_dev
                )
            else:
                pattern.avg_crowd_level = new_avg_crowd
                pattern.std_dev_crowd = new_std_dev
        
        if wait_times:
            new_avg_wait = statistics.mean(wait_times)
            if pattern.avg_wait_time:
                pattern.avg_wait_time = int(
                    (1 - self.learning_rate) * pattern.avg_wait_time +
                    self.learning_rate * new_avg_wait
                )
            else:
                pattern.avg_wait_time = int(new_avg_wait)
        
        # Update peak probability
        peak_count = sum(1 for level in crowd_levels if level > 3.5)
        pattern.peak_probability = peak_count / len(crowd_levels) if crowd_levels else 0
        
        # Update sample count and confidence
        pattern.sample_count = (pattern.sample_count or 0) + len(crowd_levels)
        pattern.confidence = min(1.0, pattern.sample_count / 30)  # Full confidence at 30 samples
        
        pattern.updated_at = datetime.utcnow()
        
        return pattern
    
    def _get_actual_crowd_level(self,
                               session: Session,
                               location_id: str,
                               forecast_time: datetime,
                               tolerance_minutes: int = 30) -> Optional[float]:
        """Get actual crowd level from reports near forecast time."""
        
        start_time = forecast_time - timedelta(minutes=tolerance_minutes)
        end_time = forecast_time + timedelta(minutes=tolerance_minutes)
        
        reports = session.query(CrowdReport).filter(
            CrowdReport.location_id == location_id,
            CrowdReport.created_at >= start_time,
            CrowdReport.created_at <= end_time,
            CrowdReport.is_verified == True
        ).all()
        
        if not reports:
            return None
        
        # Return average of verified reports
        levels = [r.crowd_level for r in reports]
        return statistics.mean(levels)
    
    def _log_model_performance(self,
                              session: Session,
                              location_id: str,
                              errors: List[float],
                              count: int):
        """Log model performance metrics."""
        
        if not errors:
            return
        
        mae = statistics.mean(errors)  # Mean Absolute Error
        rmse = (sum(e**2 for e in errors) / len(errors))**0.5  # Root Mean Square Error
        
        performance = ModelPerformance(
            model_version="1.0",
            location_id=location_id,
            mean_absolute_error=mae,
            root_mean_square_error=rmse,
            accuracy_percentage=max(0, 100 - (mae * 20)),  # Inverse error to accuracy
            period_start=datetime.utcnow() - timedelta(hours=24),
            period_end=datetime.utcnow(),
            predictions_evaluated=count
        )
        
        session.add(performance)
        session.commit()


def run_learning_cycle(session: Session) -> Dict:
    """
    Run a complete learning cycle.
    
    This should be called periodically (e.g., every hour) to:
    1. Learn from new reports
    2. Verify predictions
    3. Process user feedback
    4. Update model performance
    """
    
    learner = SelfLearningSystem()
    
    # Get all active locations
    from models import Location
    locations = session.query(Location).filter(Location.is_active == True).all()
    
    results = {
        "cycle_time": datetime.utcnow().isoformat(),
        "locations_processed": len(locations),
        "learning_results": []
    }
    
    for location in locations:
        try:
            # Learn from reports
            reports_result = learner.learn_from_reports(session, location.id)
            
            # Learn from predictions
            prediction_result = learner.learn_from_predictions(session, location.id)
            
            # Learn from feedback
            feedback_result = learner.learn_from_feedback(session, location.id)
            
            results["learning_results"].append({
                "location_id": str(location.id),
                "location_name": location.name,
                "reports": reports_result,
                "predictions": prediction_result,
                "feedback": feedback_result
            })
        except Exception as e:
            results["learning_results"].append({
                "location_id": str(location.id),
                "error": str(e)
            })
    
    return results
