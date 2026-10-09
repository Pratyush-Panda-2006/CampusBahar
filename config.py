import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env
load_dotenv()

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

    # AI & ML Configuration - Groq Cloud
    GROQ_API_KEY: Optional[str] = None
    PRIMARY_MODELS: List[str] = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "allam-2-7b"
    ]

    # AI & ML Configuration - Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_FALLBACK_MODELS: List[str] = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro"
    ]

    # Maps & Audio Services
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: str = "EXAVITQu4vr4xnSDxMaL"  # Sarah (premade, clear companion voice)

    # Ollama is completely disabled (not in use)
    USE_OLLAMA_FALLBACK: bool = False

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
GEMINI_API_KEY = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = settings.GEMINI_MODEL
GEMINI_FALLBACK_MODELS = settings.GEMINI_FALLBACK_MODELS
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY or os.getenv("GOOGLE_MAPS_API_KEY", "")
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY or os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = settings.ELEVENLABS_VOICE_ID
USE_OLLAMA_FALLBACK = False

