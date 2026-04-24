# Trend Analytics API Routes
# Time-series data and visualization endpoints

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import logging

from services.trend_analytics import TrendAnalyticsService, MetricType, AggregationPeriod

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Response Models
class TrendDataPoint(BaseModel):
    timestamp: str
    value: float
    metadata: Optional[Dict[str, Any]] = None

class TrendSeriesResponse(BaseModel):
    metric: str
    period: str
    labels: List[str]
    values: List[float]
    aggregation: str

class DashboardTrendsResponse(BaseModel):
    period_days: int
    aggregation: str
    trends: Dict[str, TrendSeriesResponse]
    generated_at: str

class ComparisonResponse(BaseModel):
    metric: str
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    change_percent: float
    trend: str

class SnapshotResponse(BaseModel):
    timestamp: str
    metrics_recorded: List[str]


@api_router.get("/dashboard")
async def get_dashboard_trends(
    days: int = Query(default=90, ge=7, le=365),
    tenant_id: str = Query(default="default")
) -> DashboardTrendsResponse:
    """
    Get trend data for all key metrics for dashboard visualization.
    
    Returns data formatted for chart.js or similar charting libraries.
    """
    try:
        service = TrendAnalyticsService(tenant_id)
        data = await service.get_dashboard_trends(days)
        
        return DashboardTrendsResponse(
            period_days=data["period_days"],
            aggregation=data["aggregation"],
            trends={
                k: TrendSeriesResponse(**v) 
                for k, v in data["trends"].items()
            },
            generated_at=data["generated_at"]
        )
    except Exception as e:
        logger.error(f"Error getting dashboard trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/metrics/{metric_type}")
async def get_metric_trend(
    metric_type: str,
    period: str = Query(default="daily", regex="^(daily|weekly|monthly|quarterly)$"),
    days: int = Query(default=30, ge=7, le=365),
    tenant_id: str = Query(default="default")
) -> TrendSeriesResponse:
    """
    Get trend data for a specific metric.
    
    Supported metrics:
    - risk_score
    - compliance_score
    - control_effectiveness
    - assessment_count
    - open_issues
    - critical_risks
    - high_risks
    - ineffective_controls
    - gap_count
    - remediation_progress
    """
    try:
        # Validate metric type
        try:
            metric = MetricType(metric_type)
        except ValueError:
            valid_metrics = [m.value for m in MetricType]
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid metric type. Valid options: {valid_metrics}"
            )
        
        # Validate period
        agg_period = AggregationPeriod(period)
        
        service = TrendAnalyticsService(tenant_id)
        series = await service.get_trend_data(metric, agg_period, days)
        chart_data = series.to_chart_data()
        
        return TrendSeriesResponse(**chart_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric trend: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/comparison/{metric_type}")
async def get_metric_comparison(
    metric_type: str,
    period_days: int = Query(default=30, ge=7, le=180),
    tenant_id: str = Query(default="default")
) -> ComparisonResponse:
    """
    Compare current period with previous period for a metric.
    
    Useful for showing improvement or decline indicators.
    """
    try:
        metric = MetricType(metric_type)
        
        service = TrendAnalyticsService(tenant_id)
        comparison = await service.get_comparison_data(metric, period_days)
        
        return ComparisonResponse(**comparison)
        
    except ValueError:
        valid_metrics = [m.value for m in MetricType]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric type. Valid options: {valid_metrics}"
        )
    except Exception as e:
        logger.error(f"Error getting comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/snapshot")
async def record_snapshot(tenant_id: str = Query(default="default")) -> SnapshotResponse:
    """
    Record a snapshot of all current metrics.
    
    This should be called periodically (e.g., daily via cron job) to track trends.
    """
    try:
        service = TrendAnalyticsService(tenant_id)
        result = await service.record_snapshot()
        
        return SnapshotResponse(**result)
        
    except Exception as e:
        logger.error(f"Error recording snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate-sample-data")
async def generate_sample_data(
    days: int = Query(default=90, ge=30, le=365),
    tenant_id: str = Query(default="default")
):
    """
    Generate sample trend data for demonstration purposes.
    
    Creates realistic-looking trend data with gradual improvements.
    """
    try:
        service = TrendAnalyticsService(tenant_id)
        result = await service.generate_sample_data(days)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Error generating sample data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/summary")
async def get_trends_summary(tenant_id: str = Query(default="default")):
    """
    Get a quick summary of all trends for executive dashboard.
    """
    try:
        service = TrendAnalyticsService(tenant_id)
        
        # Get comparisons for key metrics
        key_metrics = [
            MetricType.RISK_SCORE,
            MetricType.COMPLIANCE_SCORE,
            MetricType.CONTROL_EFFECTIVENESS,
            MetricType.OPEN_ISSUES,
            MetricType.GAP_COUNT
        ]
        
        summary = {}
        for metric in key_metrics:
            comparison = await service.get_comparison_data(metric, 30)
            summary[metric.value] = {
                "current": comparison["current_period"]["average"],
                "previous": comparison["previous_period"]["average"],
                "change_percent": comparison["change_percent"],
                "trend": comparison["trend"]
            }
        
        return {
            "period": "30 days",
            "metrics": summary,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
