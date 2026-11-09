"""API de Biblioteca de series.

Ejecutar:  uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Docs interactivas: http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import init_db
from routers import auth, series


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Biblioteca de series API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(series.router)
