#!/usr/bin/env python3

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from core.routers import routers
from db.mongodb import connect_to_mongo, close_mongo_connection
from db.redis.setup import connect_to_redis, close_redis_connection
from db.firebase.setup import init_firebase

LOGS_DIR = Path(__file__).parent / "server_logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "errors.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    await connect_to_redis()
    await asyncio.to_thread(init_firebase)
    yield
    await close_redis_connection()
    await close_mongo_connection()

app = FastAPI(
    title="FoundationX",
    description="Learning plateform for students in Rwanda",
    version="0.0.1",
    openapi_url="/swagger",
    lifespan=lifespan,
    )

routers(app=app)
