#!/usr/bin/env python3

from fastapi import FastAPI
from core.routers import routers

app = FastAPI(
    title="FoundationX",
    description="Learning plateform for students in Rwanda",
    version="0.0.1",
    openapi_url="/swagger"
    )

routers(app=app)
