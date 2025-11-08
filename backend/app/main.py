from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

from app.core.panel import router as panel_router
from app.auth.router import router as auth_router
from app.core.config import ORIGINS
from app.core.updater import start_feed_checker

@asynccontextmanager
async def lifespan(app: FastAPI):
    feed_checker_task = asyncio.create_task(start_feed_checker())
    yield
    feed_checker_task.cancel()
    try:
        await feed_checker_task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(panel_router, prefix="/panel")
app.include_router(auth_router, prefix="/auth")


@app.get("/")
async def root():
    return "Up and running!"
