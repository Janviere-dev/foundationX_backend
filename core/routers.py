#!/usr/bin/env python3

from fastapi import FastAPI
from routers.content_agent_router import router as content_router

def routers(app:FastAPI):
    app.include_router(content_router)
