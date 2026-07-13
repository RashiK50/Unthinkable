from fastapi import APIRouter

from app.api.v1 import action_items, chat, dashboard, exports, meetings, reports, transcripts

api_router = APIRouter()
api_router.include_router(meetings.router)
api_router.include_router(transcripts.router)
api_router.include_router(reports.router)
api_router.include_router(action_items.router)
api_router.include_router(chat.router)
api_router.include_router(exports.router)
api_router.include_router(dashboard.router)
