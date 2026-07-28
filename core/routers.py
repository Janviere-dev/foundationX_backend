#!/usr/bin/env python3

from fastapi import FastAPI
from routers.content_agent_router import router as content_router
from routers.assessment_router import router as assessment_router
from routers.chat import router as chat_router

def routers(app:FastAPI):
    app.include_router(content_router)
    app.include_router(assessment_router)
    app.include_router(chat_router)
