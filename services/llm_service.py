import logging
from typing import Dict, Any, Optional, List
import config

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = None
if Groq and config.GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("Groq client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Groq client: {e}")

# Local Trail Presets for ITER Bhubaneswar
TRAIL_PRESETS = {
    "khandagiri": {
        "name": "Khandagiri & Udayagiri Caves",
        "distance": "3.5 km via Jagamara",
        "transit_route": "Mo Bus Route 11 or shared auto from Jagamara Square (₹15-20)",
        "focus": "Ancient rock-cut hill trails and sweeping terrace views",
        "sensory_challenge": "Run your palms over the cool, rough 2nd-century BCE sandstone inside Rani Gumpha and feel the hilltop breeze over the temple skyline.",
        "odia_phrase": "Bhai, Khandagiri jibe ki? Kete tonka? (Brother, will you go to Khandagiri? How much?)",
        "screen_off": "Phone in pocket now—navigate the stone steps using your eyes, not a screen."
    },
    "deras": {
        "name": "Deras Dam & Chandaka Wildlife Border",
        "distance": "14 km via Pitapalli",
        "transit_route": "Shared auto or bike via Pitapalli bypass towards Chandaka border (~₹60-80)",
        "focus": "Dense forest canopy and lake reservoir breezes",
        "sensory_challenge": "Stand on the earthen dam embankment, close your eyes, and inhale the cool mist and damp bamboo forest canopy.",
        "odia_phrase": "Bhai, Chandaka Deras Dam aade jiba ki? (Brother, are you going towards Chandaka Deras Dam?)",
        "screen_off": "Turn on Airplane Mode immediately—immerse your senses in rustling sal leaves and quiet water."
    },
    "ekamra": {
        "name": "Ekamra Kanan Botanical Lake",
        "distance": "6 km, Nayapalli",
        "transit_route": "Mo Bus Route 23 or shared auto towards Nayapalli IRC Village (₹25-40)",
        "focus": "Lakeside walks, expansive grass lawns, and tree-shaded benches",
        "sensory_challenge": "Slip off your shoes and step barefoot onto the damp lakeside grass; sit beneath the mahogany tree shade.",
        "odia_phrase": "Bhai, Ekamra Kanan main gate pakhare olheibi. (Brother, please drop me at Ekamra Kanan main gate.)",
        "screen_off": "Stash the phone away—watch pelicans skim the reservoir ripples undisturbed."
    },
    "dhauli": {
        "name": "Dhauli Shanti Stupa & Daya River Bank",
        "distance": "11 km",
        "transit_route": "Mo Bus or auto via Kalpana Square towards Puri bypass (~₹35-50)",
        "focus": "River breeze, open peaceful hill walk, and historical Ashokan rock edicts",
        "sensory_challenge": "Touch the smooth white stupa railings and let the brisk Daya river breeze cool your neck.",
        "odia_phrase": "Bhai, Dhauli Shanti Stupa jiba rasta kouthi? (Brother, where is the road to Dhauli Shanti Stupa?)",
        "screen_off": "Pocket your phone—stand still for three minutes contemplating 2,200 years of peace."
    }
}


def _enforce_word_limit(text: str, max_words: int = 160) -> str:
    """Trim string strictly to max_words without breaking formatting."""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip() + "..."


def _build_deterministic_guide(
    dest_key: str,
    preset: dict,
    student_state: str,
    hour: int,
    comfort_data: dict
) -> str:
    """Zero-latency offline fallback pocket guide strictly under 160 words."""
    advisory = comfort_data.get("advisory", "Safe weather window.")
    comfort = comfort_data.get("comfort_class", "Optimal")

    guide = f"""1. Transit from ITER: Exit Jagamara Gate. Take {preset['transit_route']}.
2. Sensory Touch-Grass: {preset['sensory_challenge']} [{comfort} weather: {advisory}]
3. Odia Phrase: "{preset['odia_phrase']}"
4. Screen-Off Protocol: {preset['screen_off']}"""

    return _enforce_word_limit(guide, max_words=160)


def generate_pocket_guide(
    destination_id: str,
    student_state: str = "Hosteller",
    hour: int = 7,
    comfort_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a pocket guide strictly under 160 words targeted at out-of-state hostellers.
    Loops through config.PRIMARY_MODELS with failover to guarantee zero 404/decommission crashes.
    """
    dest_key = destination_id.lower().strip()
    preset = TRAIL_PRESETS.get(dest_key)

    if not preset:
        # Fallback to khandagiri if invalid key provided
        dest_key = "khandagiri"
        preset = TRAIL_PRESETS["khandagiri"]

    if comfort_data is None:
        comfort_data = {
            "comfort_class": "Optimal",
            "is_outdoor_safe": True,
            "advisory": "Pleasant morning coastal breeze."
        }

    comfort_class = comfort_data.get("comfort_class", "Optimal")
    advisory = comfort_data.get("advisory", "Safe trail conditions.")

    prompt = f"""You are the PravasiTrail field scout for an out-of-state college hosteller from {student_state} at ITER Bhubaneswar.
Generate a high-impact pocket guide for {preset['name']} ({preset['distance']}, {preset['focus']}) departing ITER Gate at {hour:02d}:00.
Weather Comfort: {comfort_class} ({advisory}).

Provide EXACTLY these 4 numbered items. Keep total response strictly under 140 words.
1. Transit from ITER: Mo Bus number, shared auto route, and approximate fare in ₹.
2. Sensory Touch-Grass Challenge: Specific physical sensation to experience (e.g., touch sandstone caves, feel reservoir breeze).
3. Essential Odia Driver Phrase: Conversational phrase for auto/bus conductor with English phonetic pronunciation and meaning.
4. Screen-Off Protocol: A punchy one-sentence rule telling the student to put the phone in their pocket.
No intro or outro conversational filler."""

    # Loop through config.PRIMARY_MODELS with try/except
    models_to_try = getattr(config, "PRIMARY_MODELS", [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ])

    if groq_client:
        for model in models_to_try:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a concise offline field scout guide. Never exceed 140 words."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=220
                )
                raw_text = response.choices[0].message.content.strip()
                if raw_text:
                    return _enforce_word_limit(raw_text, max_words=160)
            except Exception as err:
                logger.warning(f"Groq model '{model}' failed ({err}). Trying next configured model...")
                continue

    # Fallback to high-quality deterministic response guaranteed under 160 words
    return _build_deterministic_guide(
        dest_key=dest_key,
        preset=preset,
        student_state=student_state,
        hour=hour,
        comfort_data=comfort_data
    )


# Backward-compatible wrapper for router and full-itinerary integration
class LLMTrailScoutService:
    def get_all_trails(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": k,
                "name": v["name"],
                "distance": v["distance"],
                "focus": v["focus"],
                "transit_route": v["transit_route"],
                "highlights": [v["focus"], v["sensory_challenge"]],
                "distance_km_from_iter": 3.5 if k == "khandagiri" else (14.0 if k == "deras" else (6.0 if k == "ekamra" else 11.0)),
                "grass_score": 90
            }
            for k, v in TRAIL_PRESETS.items()
        ]

    def get_odia_phrases(self) -> List[Dict[str, Any]]:
        return [
            {
                "category": "Auto & Mo Bus Transport",
                "odia_script": "ଭାଇ, ଖଣ୍ଡଗିରି ଯିବେ କି? କେତେ ଟଙ୍କା ନେବେ?",
                "english_phonetic": "Bhai, Khandagiri jibe ki? Kete tonka nebe?",
                "meaning": "Brother, will you go to Khandagiri? How much fare?",
                "context_tip": "Standard auto fare from ITER gate is ₹20-30 shared."
            },
            {
                "category": "Street Food & Snacks",
                "odia_script": "ଭାଇ, ଗୋଟେ ପ୍ଲେଟ୍ ଦହିବରା ଆଳୁଦମ୍ ଦିଅନ୍ତୁ।",
                "english_phonetic": "Bhai, gote plate Dahibara Aloodum diantu.",
                "meaning": "Brother, give one plate Dahibara Aloodum.",
                "context_tip": "Iconic Cuttack-Bhubaneswar street food outside heritage gates."
            }
        ]

    async def generate_trail_plan(
        self,
        duration_hours: float,
        budget_inr: int,
        preferred_transit: str,
        interest: str,
        comfort_prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        dest_id = "khandagiri"
        if "lake" in interest.lower() or "grass" in interest.lower() or "botanical" in interest.lower():
            dest_id = "ekamra"
        elif "dam" in interest.lower() or "forest" in interest.lower():
            dest_id = "deras"
        elif "river" in interest.lower() or "peace" in interest.lower() or "history" in interest.lower():
            dest_id = "dhauli"

        guide = generate_pocket_guide(
            destination_id=dest_id,
            student_state="Hosteller",
            hour=comfort_prediction.get("environmental_metrics", {}).get("hour", 7),
            comfort_data=comfort_prediction
        )

        preset = TRAIL_PRESETS[dest_id]
        return {
            "destination": {
                "id": dest_id,
                "name": preset["name"],
                "distance": preset["distance"],
                "transit": preset["transit_route"],
                "grass_score": 92
            },
            "itinerary_markdown": guide,
            "generation_engine": "Groq LLM / Robust Trail Engine",
            "comfort_context": comfort_prediction,
            "curfew_advisory": "Must return to ITER hostel gate before 8:00 PM."
        }


llm_service = LLMTrailScoutService()
