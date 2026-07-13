from datetime import date

from pydantic import BaseModel


class HealthPoint(BaseModel):
    date: date
    score: float


class DashboardStats(BaseModel):
    total_meetings: int
    meetings_this_week: int
    hours_processed: float
    open_action_items: int
    overdue_action_items: int
    avg_health_score: float | None
    health_trend: list[HealthPoint]


class Insight(BaseModel):
    kind: str  # 'overdue' | 'unresolved' | 'low_health'
    message: str


class DashboardInsights(BaseModel):
    insights: list[Insight]
