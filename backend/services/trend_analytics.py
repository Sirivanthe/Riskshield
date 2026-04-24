# Trend Analytics Service
# Time-series tracking and visualization data for risk scores, compliance, and control effectiveness

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from db import db

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    RISK_SCORE = "risk_score"
    COMPLIANCE_SCORE = "compliance_score"
    CONTROL_EFFECTIVENESS = "control_effectiveness"
    ASSESSMENT_COUNT = "assessment_count"
    OPEN_ISSUES = "open_issues"
    CRITICAL_RISKS = "critical_risks"
    HIGH_RISKS = "high_risks"
    INEFFECTIVE_CONTROLS = "ineffective_controls"
    GAP_COUNT = "gap_count"
    REMEDIATION_PROGRESS = "remediation_progress"

class AggregationPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

@dataclass
class TrendDataPoint:
    """Single data point in a trend series."""
    timestamp: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TrendSeries:
    """A series of trend data points."""
    metric_type: str
    period: str
    data_points: List[TrendDataPoint]
    aggregation: str = "average"
    
    def to_chart_data(self) -> Dict[str, Any]:
        """Convert to chart-friendly format."""
        return {
            "metric": self.metric_type,
            "period": self.period,
            "labels": [dp.timestamp.strftime("%Y-%m-%d") for dp in self.data_points],
            "values": [dp.value for dp in self.data_points],
            "aggregation": self.aggregation
        }

class TrendAnalyticsService:
    """
    Service for tracking and analyzing trends over time.
    
    Features:
    - Record metric snapshots
    - Aggregate data by period
    - Generate trend analysis
    - Provide visualization data
    """
    
    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
    
    async def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        metadata: Dict[str, Any] = None,
        timestamp: datetime = None
    ) -> str:
        """Record a metric data point."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        data_point = {
            "metric_type": metric_type.value,
            "value": value,
            "timestamp": timestamp.isoformat(),
            "tenant_id": self.tenant_id,
            "metadata": metadata or {}
        }
        
        result = await db.trend_data.insert_one(data_point)
        logger.info(f"Recorded {metric_type.value}: {value}")
        return str(result.inserted_id)
    
    async def record_snapshot(self) -> Dict[str, Any]:
        """
        Record a complete snapshot of all metrics.
        Called periodically (e.g., daily) to track trends.
        """
        now = datetime.now(timezone.utc)
        metrics_recorded = []
        
        # Calculate risk score
        assessments = await db.assessments.find({}, {"_id": 0}).to_list(1000)
        if assessments:
            total_score = 0
            for assessment in assessments:
                summary = assessment.get("summary", {})
                if isinstance(summary, dict):
                    total_score += summary.get("overall_score", 70)
            avg_risk_score = total_score / len(assessments)
            await self.record_metric(MetricType.RISK_SCORE, avg_risk_score, timestamp=now)
            metrics_recorded.append("risk_score")
        
        # Calculate compliance score
        controls = await db.custom_controls.find({"status": "APPROVED"}, {"_id": 0}).to_list(1000)
        control_tests = await db.control_tests.find({"status": "APPROVED"}, {"_id": 0}).to_list(1000)
        
        if controls:
            effective = sum(1 for c in controls if c.get("effectiveness") == "EFFECTIVE")
            compliance_score = (effective / len(controls)) * 100 if controls else 0
            await self.record_metric(MetricType.COMPLIANCE_SCORE, compliance_score, timestamp=now)
            metrics_recorded.append("compliance_score")
        
        # Control effectiveness breakdown
        effectiveness_counts = {"EFFECTIVE": 0, "PARTIALLY_EFFECTIVE": 0, "INEFFECTIVE": 0, "NOT_TESTED": 0}
        for control in controls:
            eff = control.get("effectiveness", "NOT_TESTED")
            if eff in effectiveness_counts:
                effectiveness_counts[eff] += 1
        
        total_controls = len(controls) or 1
        effectiveness_rate = (effectiveness_counts["EFFECTIVE"] / total_controls) * 100
        await self.record_metric(
            MetricType.CONTROL_EFFECTIVENESS, 
            effectiveness_rate,
            metadata=effectiveness_counts,
            timestamp=now
        )
        metrics_recorded.append("control_effectiveness")
        
        # Assessment count
        assessment_count = len(assessments)
        await self.record_metric(MetricType.ASSESSMENT_COUNT, assessment_count, timestamp=now)
        metrics_recorded.append("assessment_count")
        
        # Open issues count
        open_issues = await db.issues.count_documents({"status": {"$in": ["OPEN", "IN_PROGRESS"]}})
        await self.record_metric(MetricType.OPEN_ISSUES, open_issues, timestamp=now)
        metrics_recorded.append("open_issues")
        
        # Critical and high risks
        critical_risks = 0
        high_risks = 0
        for assessment in assessments:
            for risk in assessment.get("risks", []):
                if risk.get("severity") == "CRITICAL":
                    critical_risks += 1
                elif risk.get("severity") == "HIGH":
                    high_risks += 1
        
        await self.record_metric(MetricType.CRITICAL_RISKS, critical_risks, timestamp=now)
        await self.record_metric(MetricType.HIGH_RISKS, high_risks, timestamp=now)
        metrics_recorded.extend(["critical_risks", "high_risks"])
        
        # Ineffective controls
        ineffective = effectiveness_counts.get("INEFFECTIVE", 0)
        await self.record_metric(MetricType.INEFFECTIVE_CONTROLS, ineffective, timestamp=now)
        metrics_recorded.append("ineffective_controls")
        
        # Gap count
        open_gaps = await db.control_gaps.count_documents({"status": "OPEN"})
        await self.record_metric(MetricType.GAP_COUNT, open_gaps, timestamp=now)
        metrics_recorded.append("gap_count")
        
        # Remediation progress
        remediations = await db.gap_remediations.find({}, {"_id": 0}).to_list(1000)
        if remediations:
            avg_progress = sum(r.get("progress_percentage", 0) for r in remediations) / len(remediations)
            await self.record_metric(MetricType.REMEDIATION_PROGRESS, avg_progress, timestamp=now)
            metrics_recorded.append("remediation_progress")
        
        logger.info(f"Recorded snapshot with {len(metrics_recorded)} metrics")
        return {
            "timestamp": now.isoformat(),
            "metrics_recorded": metrics_recorded
        }
    
    async def get_trend_data(
        self,
        metric_type: MetricType,
        period: AggregationPeriod = AggregationPeriod.DAILY,
        days: int = 30
    ) -> TrendSeries:
        """
        Get trend data for a specific metric.
        
        Args:
            metric_type: Type of metric to retrieve
            period: Aggregation period
            days: Number of days to look back
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        cursor = db.trend_data.find({
            "metric_type": metric_type.value,
            "timestamp": {"$gte": start_date.isoformat()}
        }, {"_id": 0}).sort("timestamp", 1)
        
        raw_data = await cursor.to_list(10000)
        
        # Aggregate by period
        aggregated = self._aggregate_data(raw_data, period)
        
        data_points = [
            TrendDataPoint(
                timestamp=datetime.fromisoformat(dp["timestamp"]) if isinstance(dp["timestamp"], str) else dp["timestamp"],
                metric_type=metric_type.value,
                value=dp["value"],
                metadata=dp.get("metadata", {})
            )
            for dp in aggregated
        ]
        
        return TrendSeries(
            metric_type=metric_type.value,
            period=period.value,
            data_points=data_points
        )
    
    def _aggregate_data(
        self, 
        raw_data: List[Dict], 
        period: AggregationPeriod
    ) -> List[Dict]:
        """Aggregate raw data points by period."""
        if not raw_data:
            return []
        
        # Group by period
        groups: Dict[str, List[float]] = {}
        
        for dp in raw_data:
            ts = dp["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            
            if period == AggregationPeriod.DAILY:
                key = ts.strftime("%Y-%m-%d")
            elif period == AggregationPeriod.WEEKLY:
                # Week number
                key = ts.strftime("%Y-W%W")
            elif period == AggregationPeriod.MONTHLY:
                key = ts.strftime("%Y-%m")
            elif period == AggregationPeriod.QUARTERLY:
                quarter = (ts.month - 1) // 3 + 1
                key = f"{ts.year}-Q{quarter}"
            else:
                key = ts.strftime("%Y-%m-%d")
            
            if key not in groups:
                groups[key] = []
            groups[key].append(dp["value"])
        
        # Calculate averages
        result = []
        for key in sorted(groups.keys()):
            values = groups[key]
            avg_value = sum(values) / len(values)
            
            # Convert key back to timestamp
            if period == AggregationPeriod.DAILY:
                ts = datetime.strptime(key, "%Y-%m-%d")
            elif period == AggregationPeriod.WEEKLY:
                ts = datetime.strptime(key + "-1", "%Y-W%W-%w")
            elif period == AggregationPeriod.MONTHLY:
                ts = datetime.strptime(key + "-01", "%Y-%m-%d")
            elif period == AggregationPeriod.QUARTERLY:
                year, q = key.split("-Q")
                month = (int(q) - 1) * 3 + 1
                ts = datetime(int(year), month, 1)
            else:
                ts = datetime.strptime(key, "%Y-%m-%d")
            
            result.append({
                "timestamp": ts.replace(tzinfo=timezone.utc).isoformat(),
                "value": round(avg_value, 2)
            })
        
        return result
    
    async def get_dashboard_trends(self, days: int = 90) -> Dict[str, Any]:
        """
        Get all trend data for dashboard visualization.
        
        Returns data formatted for chart.js or similar libraries.
        """
        metrics = [
            MetricType.RISK_SCORE,
            MetricType.COMPLIANCE_SCORE,
            MetricType.CONTROL_EFFECTIVENESS,
            MetricType.OPEN_ISSUES,
            MetricType.CRITICAL_RISKS,
            MetricType.GAP_COUNT
        ]
        
        trends = {}
        for metric in metrics:
            series = await self.get_trend_data(metric, AggregationPeriod.WEEKLY, days)
            trends[metric.value] = series.to_chart_data()
        
        return {
            "period_days": days,
            "aggregation": "weekly",
            "trends": trends,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_comparison_data(
        self,
        metric_type: MetricType,
        current_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comparison between current and previous period.
        Useful for showing improvement/decline.
        """
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=current_period_days)
        previous_start = current_start - timedelta(days=current_period_days)
        
        # Current period
        current_data = await db.trend_data.find({
            "metric_type": metric_type.value,
            "timestamp": {"$gte": current_start.isoformat()}
        }, {"_id": 0}).to_list(10000)
        
        # Previous period
        previous_data = await db.trend_data.find({
            "metric_type": metric_type.value,
            "timestamp": {
                "$gte": previous_start.isoformat(),
                "$lt": current_start.isoformat()
            }
        }, {"_id": 0}).to_list(10000)
        
        current_avg = sum(d["value"] for d in current_data) / len(current_data) if current_data else 0
        previous_avg = sum(d["value"] for d in previous_data) / len(previous_data) if previous_data else 0
        
        if previous_avg > 0:
            change_percent = ((current_avg - previous_avg) / previous_avg) * 100
        else:
            change_percent = 0
        
        return {
            "metric": metric_type.value,
            "current_period": {
                "start": current_start.isoformat(),
                "end": now.isoformat(),
                "average": round(current_avg, 2),
                "data_points": len(current_data)
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": current_start.isoformat(),
                "average": round(previous_avg, 2),
                "data_points": len(previous_data)
            },
            "change_percent": round(change_percent, 2),
            "trend": "improving" if change_percent > 0 else "declining" if change_percent < 0 else "stable"
        }
    
    async def generate_sample_data(self, days: int = 90):
        """Generate sample trend data for demonstration."""
        import random
        
        base_values = {
            MetricType.RISK_SCORE: 65,
            MetricType.COMPLIANCE_SCORE: 70,
            MetricType.CONTROL_EFFECTIVENESS: 75,
            MetricType.ASSESSMENT_COUNT: 20,
            MetricType.OPEN_ISSUES: 15,
            MetricType.CRITICAL_RISKS: 3,
            MetricType.HIGH_RISKS: 8,
            MetricType.INEFFECTIVE_CONTROLS: 5,
            MetricType.GAP_COUNT: 10,
            MetricType.REMEDIATION_PROGRESS: 50
        }
        
        trends = {
            MetricType.RISK_SCORE: 0.15,  # Improving (higher is better)
            MetricType.COMPLIANCE_SCORE: 0.12,
            MetricType.CONTROL_EFFECTIVENESS: 0.10,
            MetricType.ASSESSMENT_COUNT: 0.08,
            MetricType.OPEN_ISSUES: -0.05,  # Declining is good
            MetricType.CRITICAL_RISKS: -0.10,
            MetricType.HIGH_RISKS: -0.08,
            MetricType.INEFFECTIVE_CONTROLS: -0.12,
            MetricType.GAP_COUNT: -0.10,
            MetricType.REMEDIATION_PROGRESS: 0.20
        }
        
        now = datetime.now(timezone.utc)
        
        for metric_type, base_value in base_values.items():
            trend_factor = trends.get(metric_type, 0)
            
            for day in range(days, 0, -1):
                timestamp = now - timedelta(days=day)
                
                # Calculate value with trend and noise
                progress = (days - day) / days
                trend_adjustment = base_value * trend_factor * progress
                noise = random.uniform(-2, 2)
                
                value = base_value + trend_adjustment + noise
                
                # Clamp values
                if metric_type in [MetricType.RISK_SCORE, MetricType.COMPLIANCE_SCORE, 
                                   MetricType.CONTROL_EFFECTIVENESS, MetricType.REMEDIATION_PROGRESS]:
                    value = max(0, min(100, value))
                else:
                    value = max(0, value)
                
                await self.record_metric(metric_type, round(value, 2), timestamp=timestamp)
        
        logger.info(f"Generated {days * len(base_values)} sample trend data points")
        return {"message": f"Generated sample data for {days} days"}
