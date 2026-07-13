from fastapi import APIRouter

from app.api.deps import DashboardServiceDep, UserDep
from app.schemas.dashboard import DashboardInsights, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def stats(user: UserDep, service: DashboardServiceDep) -> DashboardStats:
    return await service.stats(user)


@router.get("/insights", response_model=DashboardInsights)
async def insights(user: UserDep, service: DashboardServiceDep) -> DashboardInsights:
    return await service.insights(user)
