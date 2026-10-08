import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "PravasiTrail (CampusBahar)"
    PROJECT_SLOGAN: str = "Offline Trail & Heritage Scout for Out-of-State Hostellers at ITER Bhubaneswar"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Campus Anchor: ITER, Siksha 'O' Anusandhan (SOA), Jagamara
    CAMPUS_NAME: str = "Institute of Technical Education and Research (ITER), SOA"
    CAMPUS_LAT: float = 20.2520
    CAMPUS_LON: float = 85.7956
    CAMPUS_ADDRESS: str = "Jagamara, Khandagiri, Bhubaneswar, Odisha 751030"
    HOSTEL_CURFEW_HOUR: int = 20  # 8:00 PM typical in-time

    # Paths
    DATA_PATH: Path = BASE_DIR / "data" / "bbsr_weather_comfort.csv"

    # AI & ML Configuration
    GROQ_API_KEY: Optional[str] = None
    PRIMARY_MODELS: list = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    USE_OLLAMA_FALLBACK: bool = True

    # TabPFN / ML Inference
    TABPFN_DEVICE: str = "cpu"
    TABPFN_N_ENSEMBLE: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Direct module-level exports for convenient access
GROQ_API_KEY = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
PRIMARY_MODELS = settings.PRIMARY_MODELS

