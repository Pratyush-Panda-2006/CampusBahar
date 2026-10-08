import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from services.tabpfn_service import predict_comfort_window, tabpfn_service
from services.llm_service import generate_pocket_guide, TRAIL_PRESETS, llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["scout"])


class ScoutRequest(BaseModel):
    destination: str = Field(
        default="khandagiri",
        description="Destination ID: 'khandagiri', 'deras', 'ekamra', 'dhauli'"
    )
    target_hour: int = Field(
        default=7,
        ge=0,
        le=23,
        description="Target scout hour of the day (0 to 23)"
    )
    student_home_state: str = Field(
        default="Jharkhand",
        description="Home state of the out-of-state hosteller (e.g. Jharkhand, Bihar, UP)"
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
        # 5 to 8 AM: 24-27°C, 85% humidity, 1-3 UV
        temp = round(24.0 + (hour - 5) * 1.0, 1)
        humidity = 85.0
        uv = round(1.0 + (hour - 5) * 0.7, 1)
    elif 9 <= hour <= 15:
        # 9 AM to 3 PM: 31-35°C, 55% humidity, 7-10 UV
        offset = 3.0 - abs(hour - 12) * 0.4
        temp = round(32.0 + offset, 1)
        humidity = 55.0
        uv = round(10.0 - abs(hour - 12) * 0.7, 1)
    elif 16 <= hour <= 19:
        # 4 to 7 PM: 27-29°C, 75% humidity, 0-2 UV
        temp = round(29.0 - (hour - 16) * 0.6, 1)
        humidity = 75.0
        uv = round(max(0.0, 2.0 - (hour - 16) * 0.7), 1)
    else:
        # Night: 25°C, 85% humidity, 0 UV
        temp = 25.0
        humidity = 85.0
        uv = 0.0

    return {"temp": temp, "humidity": humidity, "uv": uv}


@router.post("/scout", summary="Generate Complete PravasiTrail Scout Card")
def scout_trail(request: ScoutRequest):
    """
    Core scout endpoint:
      1. Estimates Bhubaneswar October weather for the target hour.
      2. Computes TabPFN / heuristic comfort class.
      3. Synthesizes a <= 160-word cultural & sensory pocket guide.
    """
    dest_key = request.destination.lower().strip()
    preset = TRAIL_PRESETS.get(dest_key)
    if not preset:
        preset = TRAIL_PRESETS.get("khandagiri")
        destination_name = "Khandagiri & Udayagiri Caves"
    else:
        destination_name = preset["name"]

    # 1. Weather estimation
    weather = estimate_bbsr_weather(request.target_hour)

    # 2. Predict comfort window
    comfort_dict = predict_comfort_window(
        hour=request.target_hour,
        temp=weather["temp"],
        humidity=weather["humidity"],
        uv=weather["uv"]
    )

    # 3. Generate pocket guide
    card_markdown = generate_pocket_guide(
        destination_id=dest_key,
        student_state=request.student_home_state,
        hour=request.target_hour,
        comfort_data=comfort_dict
    )

    return {
        "status": "success",
        "destination": destination_name,
        "comfort": comfort_dict,
        "weather": {
            "temp": weather["temp"],
            "humidity": weather["humidity"],
            "uv": weather["uv"]
        },
        "card_markdown": card_markdown
    }


@router.get("/health", summary="Health check endpoint")
def health_status():
    return {
        "status": "healthy",
        "service": "PravasiTrail API"
    }


# Preserved auxiliary endpoints for frontend & inspection
@router.get("/trails", summary="List Available Trails")
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
