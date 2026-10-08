import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from services.tabpfn_service import predict_comfort_window, tabpfn_service
from services.llm_service import generate_pocket_guide, translate_text, TRAIL_PRESETS, llm_service
from services.transit_service import (
    CAMPUS_HUBS,
    DESTINATIONS_DATA,
    compute_transit_matrix
)
from services.audio_service import generate_elevenlabs_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scout"])


class TranslationRequest(BaseModel):
    text: str = Field(..., description="Text to translate between English and Odia", min_length=1)
    direction: str = Field(
        default="en-to-or",
        description="Translation direction: 'en-to-or' (English to Odia) or 'or-to-en' (Odia to English)"
    )


class SpeakRequest(BaseModel):
    text: str = Field(..., description="Pocket guide markdown or text to narrate", min_length=1)
    voice_id: Optional[str] = Field(default=None, description="Optional ElevenLabs voice ID")


class ScoutRequest(BaseModel):
    origin_campus: str = Field(
        default="iter",
        description="Origin campus ID: 'iter', 'kiit', 'outr', 'aiims', 'utkal', 'silicon', 'cvraman'"
    )
    destination: str = Field(
        default="khandagiri",
        description="Destination ID: e.g. 'khandagiri', 'deras', 'ekamra', 'dhauli', 'mukteswara', 'tribal', 'kalabhoomi'"
    )
    target_hour: int = Field(
        default=7,
        ge=0,
        le=23,
        description="Target scout hour of the day (0 to 23)"
    )



def estimate_bbsr_weather(hour: int) -> Dict[str, float]:
    """
    Estimate typical Bhubaneswar meteorological metrics based on diurnal cycle:
      - 5 to 8 AM: 24-27°C, 85% humidity, 1-3 UV
      - 9 AM to 3 PM: 31-35°C, 55% humidity, 7-10 UV
      - 4 to 7 PM: 27-29°C, 75% humidity, 0-2 UV
      - Night: 25°C, 85% humidity, 0 UV
    """
    if 5 <= hour <= 8:
        temp = round(24.0 + (hour - 5) * 1.0, 1)
        humidity = 85.0
        uv = round(1.0 + (hour - 5) * 0.7, 1)
    elif 9 <= hour <= 15:
        offset = 3.0 - abs(hour - 12) * 0.4
        temp = round(32.0 + offset, 1)
        humidity = 55.0
        uv = round(10.0 - abs(hour - 12) * 0.7, 1)
    elif 16 <= hour <= 19:
        temp = round(29.0 - (hour - 16) * 0.6, 1)
        humidity = 75.0
        uv = round(max(0.0, 2.0 - (hour - 16) * 0.7), 1)
    else:
        temp = 25.0
        humidity = 85.0
        uv = 0.0

    return {"temp": temp, "humidity": humidity, "uv": uv}


@router.post("/scout", summary="Generate Complete PravasiTrail Scout Card with Multi-Campus Transit & Maps")
def scout_trail(request: ScoutRequest):
    """
    Core scout endpoint:
      1. Estimates Bhubaneswar October weather for the target hour.
      2. Computes TabPFN / heuristic comfort class.
      3. Computes 4-mode comparative transit fare & route matrix from origin campus.
      4. Synthesizes a <= 160-word cultural & sensory pocket guide tailored to campus origin.
      5. Provides interactive Google Maps embed & directions URLs.
    """
    dest_key = request.destination.lower().strip()
    preset = TRAIL_PRESETS.get(dest_key, TRAIL_PRESETS["khandagiri"])
    destination_name = preset["name"]
    campus_key = request.origin_campus.lower().strip()

    # 1. Weather estimation
    weather = estimate_bbsr_weather(request.target_hour)

    # 2. Predict comfort window with TabPFN
    comfort_dict = predict_comfort_window(
        hour=request.target_hour,
        temp=weather["temp"],
        humidity=weather["humidity"],
        uv=weather["uv"]
    )

    # 3. Compute Multi-Modal Transit Fare & Route Matrix
    transit_matrix = compute_transit_matrix(
        origin_campus_id=campus_key,
        destination_id=dest_key
    )

    # 4. Generate AI pocket field guide tailored to campus
    card_markdown = generate_pocket_guide(
        destination_id=dest_key,
        origin_campus=campus_key,
        student_state="Hosteller",
        hour=request.target_hour,
        comfort_data=comfort_dict
    )

    return {
        "status": "success",
        "destination": destination_name,
        "destination_id": dest_key,
        "origin_campus": transit_matrix["origin_campus"],
        "comfort": comfort_dict,
        "weather": {
            "temp": weather["temp"],
            "humidity": weather["humidity"],
            "uv": weather["uv"]
        },
        "distance_km": transit_matrix["distance_km"],
        "transit_modes": transit_matrix["modes"],
        "maps": transit_matrix["maps"],
        "card_markdown": card_markdown
    }


@router.get("/campuses", summary="List All Supported Bhubaneswar University Hubs")
def get_campuses():
    return {
        "campuses": list(CAMPUS_HUBS.values())
    }


@router.get("/destinations", summary="List All 10 Curated Outdoor Destinations")
def get_destinations():
    return {
        "destinations": list(DESTINATIONS_DATA.values())
    }


@router.get("/health", summary="Health check endpoint")
def health_status():
    return {
        "status": "healthy",
        "service": "PravasiTrail Multi-Campus Outdoor Engine"
    }


@router.get("/trails", summary="List Available Trails with Full Metadata")
def get_trails():
    return {
        "trails": [
            {"id": k, **v} for k, v in TRAIL_PRESETS.items()
        ]
    }


@router.get("/comfort/forecast", summary="24-Hour Forecast Matrix")
def get_comfort_forecast():
    return {
        "hourly_matrix": tabpfn_service.get_full_day_matrix()
    }


@router.post("/translate", summary="Translate text between English and Odia with speech-ready phonetic breakdown")
def translate_endpoint(request: TranslationRequest):
    """
    Bidirectional English <-> Odia translator powered by Gemini Flash / Groq LLM
    with phonetic romanization, spoken script, and local cultural survival tips.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    result = translate_text(text=request.text.strip(), direction=request.direction)
    return {
        "status": "success",
        **result
    }


@router.post("/speak", summary="Synthesize trail guide speech via ElevenLabs audio companion")
def speak_endpoint(request: SpeakRequest):
    """
    Generate natural audio narration using ElevenLabs text-to-speech companion.
    Falls back gracefully to browser SpeechSynthesis if API key is not configured.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    result = generate_elevenlabs_audio(text=request.text.strip(), voice_id=request.voice_id)
    return result


