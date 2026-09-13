import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import documents, operations, signatures, audit, export, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="ILovePDF Personal Replacement API",
    description="Local, private, auditable PDF management and simple e-signature engine.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(operations.router)
app.include_router(signatures.router)
app.include_router(audit.router)
app.include_router(export.router)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ILovePDF Personal Local Engine",
        "storage_dir": settings.STORAGE_DIR
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server Error: {str(exc)}"}
    )
