from fastapi import APIRouter

from app.auth.discord import router as discord_router

router = APIRouter()

router.include_router(
    discord_router,
    prefix="/discord",
)
