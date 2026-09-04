"""
WaitWise anomaly detection.

Flags statistically unusual crowd reports without automatically deleting them.
Suspicious reports remain available for verification and human review.
"""

from datetime import datetime, timedelta
from typing import Optional
import statistics

from sqlalchemy.orm import Session
from models import CrowdReport


class AnomalyDetector:
    MIN_BASELINE_SAMPLES = 5

    def __init__(self, session: Session):
        self.session = session

    def _recent_verified(self, location_id, hours: int = 24, limit: int = 100):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.session.query(CrowdReport)
            .filter(
                CrowdReport.location_id == location_id,
                CrowdReport.is_verified.is_(True),
                CrowdReport.created_at >= cutoff,
            )
            .order_by(CrowdReport.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def _z_score(value: float, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = statistics.mean(values)
        std = statistics.pstdev(values)
        if std == 0:
            return 0.0 if value == mean else float("inf")
        return abs((value - mean) / std)

    def analyze(self, location_id, crowd_level: Optional[float], wait_time_minutes: Optional[float]):
        reports = self._recent_verified(location_id)
        crowd_values = [float(r.crowd_level) for r in reports if r.crowd_level is not None]
        wait_values = [float(r.wait_time_minutes) for r in reports if r.wait_time_minutes is not None]

        flags = []
        details = {}

        if crowd_level is not None and len(crowd_values) >= self.MIN_BASELINE_SAMPLES:
            z = self._z_score(float(crowd_level), crowd_values)
            details["crowd"] = {
                "baseline_samples": len(crowd_values),
                "recent_average": round(statistics.mean(crowd_values), 3),
                "z_score": round(z, 3) if z != float("inf") else None,
            }
            if z >= 3:
                flags.append("unusual_crowd_level")

        if wait_time_minutes is not None and len(wait_values) >= self.MIN_BASELINE_SAMPLES:
            z = self._z_score(float(wait_time_minutes), wait_values)
            details["wait_time"] = {
                "baseline_samples": len(wait_values),
                "recent_average": round(statistics.mean(wait_values), 3),
                "z_score": round(z, 3) if z != float("inf") else None,
            }
            if z >= 3:
                flags.append("unusual_wait_time")

        severity = "high" if len(flags) >= 2 else "medium" if flags else "normal"
        return {
            "is_anomaly": bool(flags),
            "severity": severity,
            "flags": flags,
            "details": details,
            "baseline_available": bool(details),
        }
