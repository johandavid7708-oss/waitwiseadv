from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import CrowdReport


class CrowdService:
    def __init__(self, session: Session):
        self.session = session

    def get_verified_reports(self, location_id, limit: int = 500):
        return (
            self.session.query(CrowdReport)
            .filter(
                CrowdReport.location_id == location_id,
                CrowdReport.is_verified.is_(True),
            )
            .order_by(CrowdReport.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_current_crowd(self, location_id, hours: int = 2):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        reports = (
            self.session.query(CrowdReport)
            .filter(
                CrowdReport.location_id == location_id,
                CrowdReport.created_at >= cutoff,
                CrowdReport.is_verified.is_(True),
            )
            .order_by(CrowdReport.created_at.desc())
            .all()
        )

        if not reports:
            return {
                "available": False,
                "crowd_level": None,
                "wait_time_minutes": None,
                "confidence": 0.0,
                "report_count": 0,
            }

        crowds = [r.crowd_level for r in reports if r.crowd_level is not None]
        waits = [r.wait_time_minutes for r in reports if r.wait_time_minutes is not None]

        return {
            "available": True,
            "crowd_level": round(sum(crowds) / len(crowds), 3) if crowds else None,
            "wait_time_minutes": round(sum(waits) / len(waits), 2) if waits else None,
            "confidence": round(min(1.0, len(reports) / 20), 3),
            "report_count": len(reports),
            "latest_report_at": reports[0].created_at.isoformat(),
        }

    def get_crowd_trend(self, location_id, hours: int = 6):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        reports = (
            self.session.query(CrowdReport)
            .filter(
                CrowdReport.location_id == location_id,
                CrowdReport.created_at >= cutoff,
                CrowdReport.is_verified.is_(True),
            )
            .order_by(CrowdReport.created_at.asc())
            .all()
        )
        levels = [r.crowd_level for r in reports if r.crowd_level is not None]
        if len(levels) < 2:
            return {"trend": "unknown", "change": 0.0, "samples": len(levels)}

        change = levels[-1] - levels[0]
        trend = "rising" if change > 0.25 else "falling" if change < -0.25 else "stable"
        return {"trend": trend, "change": round(change, 3), "samples": len(levels)}
