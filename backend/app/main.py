from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import async_engine, Base
from app.api import (
    core_router,
    demo_router,
    scenarios_router,
    simulation_router,
    websocket_router,
    llm_router,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting WardOps Backend...")
    
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down WardOps Backend...")
    await async_engine.dispose()


app = FastAPI(
    title="WardOps Digital Twin API",
    description="Hospital Operations Command Center - Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "message": str(exc)}
    )


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "wardops-backend"}


# API info
@app.get("/")
async def root():
    return {
        "name": "WardOps Digital Twin API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(core_router, prefix="/api", tags=["Core"])
app.include_router(demo_router, prefix="/api/demo", tags=["Demo"])
app.include_router(scenarios_router, prefix="/api/scenarios", tags=["Scenarios"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
app.include_router(websocket_router, prefix="/api/ws", tags=["WebSocket"])
app.include_router(llm_router, prefix="/api/copilot", tags=["Copilot"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
