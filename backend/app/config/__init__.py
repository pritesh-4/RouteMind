"""
Configuration module for RouteMind Backend.
Centralizes environment variables, CORS settings, and application metadata.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Build paths relative to this file: __file__ is app/config/__init__.py, so parent.parent.parent is backend root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the .env file in the backend root
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseModel):
    """
    Application settings container validated by Pydantic.
    Centralizes all app level configurations.
    """

    APP_NAME: str = os.getenv("APP_NAME", "RouteMind")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    ENV: str = os.getenv("ENV", "development")

    # CORS Origins - parsed as list of strings
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8000,https://routemind-ai-app.vercel.app",
        ).split(",")
        if origin.strip()
    ]

    # API Keys (loaded from environment)
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY") or None
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY") or None
    NVIDIA_NIM_API_KEY: str | None = os.getenv("NVIDIA_NIM_API_KEY") or None
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY") or None


# Global settings instance for import across the codebase
settings = Settings()
