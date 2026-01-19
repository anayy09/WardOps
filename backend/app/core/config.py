from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/wardops"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/wardops"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # API
    API_PREFIX: str = "/api"
    
    # LLM
    LLM_API_URL: str = "https://api.openai.com/v1/chat/completions"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    
    # Simulation
    MAX_SIMULATION_TIME_SECONDS: int = 300
    DEFAULT_SEED: int = 42
    
    class Config:
        env_file = ".env.local"
        case_sensitive = True


settings = Settings()
