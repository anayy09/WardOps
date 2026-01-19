from app.api.routes import router as core_router
from app.api.demo import router as demo_router
from app.api.scenarios import router as scenarios_router
from app.api.simulation import router as simulation_router
from app.api.websocket import router as websocket_router
from app.api.llm import router as llm_router

__all__ = [
    "core_router",
    "demo_router", 
    "scenarios_router",
    "simulation_router",
    "websocket_router",
    "llm_router",
]
