import logging
from typing import Dict, Any, Optional, List
import config
from services.transit_service import CAMPUS_HUBS, DESTINATIONS_DATA

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

# Initialize Groq client
groq_client = None
if Groq and config.GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("Groq client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Groq client: {e}")

# Initialize Google Gemini client
gemini_model = None
if genai and config.GEMINI_API_KEY:
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Gemini client initialized with model '{config.GEMINI_MODEL}'.")
    except Exception as e:
        logger.warning(f"Could not initialize Gemini client: {e}")

# Curated 10 Outdoor Destinations across Bhubaneswar
TRAIL_PRESETS: Dict[str, Dict[str, Any]] = {
    "khandagiri": {
        "name": "Khandagiri & Udayagiri Caves",
        "category": "Hills & Caves",
        "distance": "3.5 km from West Hubs",
        "focus": "Ancient sandstone rock caves, sweeping city views, early morning mist",
        "sensory_challenge": "Run your palms over the cool, rough 2nd-century BCE sandstone inside Rani Gumpha and feel the hilltop breeze over the temple skyline.",
        "odia_phrase": "Bhai, Khandagiri jibe ki? Kete tonka? (Brother, will you go to Khandagiri? How much?)",
        "screen_off": "Phone in pocket now—navigate the stone steps using your eyes, not a screen."
    },
    "deras": {
        "name": "Deras & Jhumka Dam (Chandaka Wildlife Sanctuary)",
        "category": "Lakes & Reserves",
        "distance": "12–16 km via Chandaka Road",
        "focus": "Lakeside eco-walks, dense forest fringe, calm reservoir breeze",
        "sensory_challenge": "Stand on the earthen dam embankment, close your eyes, and inhale the cool mist and damp bamboo forest canopy.",
        "odia_phrase": "Bhai, Chandaka Deras Dam aade jiba ki? (Brother, are you going towards Chandaka Deras Dam?)",
        "screen_off": "Turn on Airplane Mode immediately—immerse your senses in rustling sal leaves and quiet water."
    },
    "ekamra": {
        "name": "Ekamra Kanan Botanical Lake (Nayapalli)",
        "category": "Lakes & Reserves",
        "distance": "5–8 km, Central North",
        "focus": "Massive walking perimeter, rose gardens, shaded lawns, pelican wetlands",
        "sensory_challenge": "Slip off your shoes and step barefoot onto the damp lakeside grass; sit beneath the mahogany tree shade.",
        "odia_phrase": "Bhai, Ekamra Kanan main gate pakhare olheibi. (Brother, please drop me at Ekamra Kanan main gate.)",
        "screen_off": "Stash the phone away—watch pelicans skim the reservoir ripples undisturbed."
    },
    "dhauli": {
        "name": "Dhauli Shanti Stupa & Daya Riverbank",
        "category": "Heritage & Culture",
        "distance": "11–15 km via Puri Highway",
        "focus": "Peaceful white pagoda, open breeze along historical Daya riverbanks",
        "sensory_challenge": "Touch the smooth white stupa railings and let the brisk Daya river breeze cool your neck.",
        "odia_phrase": "Bhai, Dhauli Shanti Stupa jiba rasta kouthi? (Brother, where is the road to Dhauli Shanti Stupa?)",
        "screen_off": "Pocket your phone—stand still for three minutes contemplating 2,200 years of peace."
    },
    "nandankanan": {
        "name": "Nandankanan Botanical Garden (Kanjia Lake)",
        "category": "Lakes & Reserves",
        "distance": "8–18 km north via Patia",
        "focus": "Forest boardwalks, wetlands, birdwatching canopy, fresh freshwater breezes",
        "sensory_challenge": "Lean over the wooden lake bridge at Kanjia Lake; listen to egrets calling and breathe in sweet aquatic lotus mist.",
        "odia_phrase": "Bhai, Botanical Garden gate pakhare rokhantu. (Brother, stop near the Botanical Garden gate.)",
        "screen_off": "Ditch digital maps—track trail markers made of carved wooden posts along the wetland shore."
    },
    "jayadev": {
        "name": "Jayadev Vatika Forest Park",
        "category": "Hills & Caves",
        "distance": "3–6 km, Khandagiri Foothills",
        "focus": "50+ acre landscaped park with forested walking trails, rocks, and streamlets",
        "sensory_challenge": "Scramble up the rocky outcrop near the natural streamlet; feel the textured granite and cool shaded ravine air.",
        "odia_phrase": "Bhai, Jayadev Vatika pakhare gote auto milibo ki? (Brother, will an auto be available near Jayadev Vatika?)",
        "screen_off": "Tuck phone away—follow the forest trail by listening to the babbling brook and songbirds."
    },
    "bindusagar": {
        "name": "Bindu Sagar Heritage Corridor (Old Town)",
        "category": "Heritage & Culture",
        "distance": "6–10 km, Heritage Precinct",
        "focus": "Sacred lake perimeter stroll, 1,000-year-old temple architecture, peaceful stone ghats",
        "sensory_challenge": "Sit on the carved laterite stone ghats of Bindu Sagar at dawn; feel the gentle surface breeze reflecting temple spires.",
        "odia_phrase": "Mousa, Bindu Sagar ghat kouthi achi? (Uncle, where is the Bindu Sagar ghat?)",
        "screen_off": "No selfie breaks—observe the saffron morning light reflecting off Lingaraj temple's pinnacle."
    },
    "ekamrahaat": {
        "name": "Ekamra Haat & Native Tree Avenues",
        "category": "Heritage & Culture",
        "distance": "4–8 km, Unit-3 Heart",
        "focus": "Open-air craft trails, native tree avenues, Odia culinary stalls, calm garden benches",
        "sensory_challenge": "Cup a warm clay bhar of spiced tea from an artisan stall and breathe in rain-washed mahogany tree bark aromas.",
        "odia_phrase": "Bhai, gote garam chaa au Chenna Poda diantu. (Brother, please give hot tea and a slice of Chenna Poda.)",
        "screen_off": "Phone silent—talk directly to local patachitra artisans hand-painting palm leaves."
    },
    "barunei": {
        "name": "Barunei Hill & Perennial Stream",
        "category": "Hills & Caves",
        "distance": "14–24 km, Khordha Hill Range",
        "focus": "Moderate rocky climb, fresh water perennial springs, dense sal tree canopy",
        "sensory_challenge": "Dip your hands into the ice-cold perennial hill stream 'Swarna Ganga' cascading over polished mountain pebbles.",
        "odia_phrase": "Bhai, Barunei pahada chhadiki auto kete tanka? (Brother, how much for auto up to Barunei hill?)",
        "screen_off": "Zero connectivity bliss—navigate the boulder trail relying on physical balance and focus."
    },
    "kuakhai": {
        "name": "Kuakhai Riverfront & Bali Jatra Grounds",
        "category": "Open Horizons",
        "distance": "6–14 km east, River Bed",
        "focus": "Wide open riverbed horizons, sunset breeze, dirt paths, evening sky reflections",
        "sensory_challenge": "Kick off sneakers and walk across the fine river sandbar as the sunset sea-breeze sweeps across the water channel.",
        "odia_phrase": "Bhai, Hanspal bridge aade jibe ki? (Brother, will you go towards Hanspal bridge?)",
        "screen_off": "Eyes on the horizon—watch flocking herons cross the twilight sky without a camera lens."
    },
    "sisupalgarh": {
        "name": "Sisupalgarh Fortified Ancient Ruins",
        "category": "Heritage & Culture",
        "distance": "6–12 km, Southeast Ramparts",
        "focus": "2,500-year-old fortified ramparts, monolithic stone pillars, quiet sunset horizon walks",
        "sensory_challenge": "Walk atop the 25-foot ancient laterite earth ramparts and feel the wide open valley breeze across the surrounding green paddy horizons.",
        "odia_phrase": "Bhai, Sisupalgarh pillar pakhare gote auto miliba ki? (Brother, will an auto be available near Sisupalgarh pillar?)",
        "screen_off": "Step away from digital feeds—walk among monolithic carved pillars that stood before Alexander reached India."
    },
    "lingaraj": {
        "name": "Lingaraj Temple & Ekamra Kshetra Heritage Circuit",
        "category": "Heritage & Culture",
        "distance": "5–14 km, Old Town Sacred Core",
        "focus": "11th-century Kalinga sandstone tower, ancient sacred courtyards, holy silence",
        "sensory_challenge": "Stand barefoot on the stone perimeter flagstones under the towering 180-foot deula spire; inhale camphor, marigolds, and sea air.",
        "odia_phrase": "Mousa, Lingaraj Mandira uttar dwar kouthi? (Uncle, where is the north gate of Lingaraj Temple?)",
        "screen_off": "Phones are prohibited inside the inner complex—embrace the complete digital disconnect."
    },
    "chausathi": {
        "name": "Chausathi Yogini Temple & Enclosure (Hirapur)",
        "category": "Heritage & Culture",
        "distance": "12–18 km, Hirapur Riverbank",
        "focus": "Rare 9th-century open-air circular hypaethral shrine overlooking peaceful paddy fields",
        "sensory_challenge": "Step inside the roofless circular chlorite shrine open to the sky; run fingers across intricate black stone carvings in utter serenity.",
        "odia_phrase": "Bhai, Hirapur Chausathi Yogini mandira aade jibe ki? (Brother, will you go towards Hirapur Chausathi Yogini temple?)",
        "screen_off": "Stand in the circular sanctum under open clouds without looking at a device."
    },
    "rprc": {
        "name": "Regional Plant Resource Centre (Cactus Garden)",
        "category": "Lakes & Reserves",
        "distance": "5–9 km, Nayapalli",
        "focus": "Asia's largest cactus conservatory, lakeside walking perimeter, shaded bamboo groves",
        "sensory_challenge": "Stroll along the silent wetland boardwalk among water lilies and towering century-old mahogany and bamboo clusters.",
        "odia_phrase": "Bhai, Cactus Garden main gate pakhare rokhantu. (Brother, stop near the Cactus Garden main gate.)",
        "screen_off": "Put phone on silent—observe iridescent kingfishers dive for fish in the conservatory lake."
    },
    "atri": {
        "name": "Atri Hot Sulphur Springs & Nature Walk",
        "category": "Hills & Caves",
        "distance": "22–38 km, Khordha Countryside",
        "focus": "Natural bubbling thermal springs, countryside mango orchards, healing mineral waters",
        "sensory_challenge": "Dip your palms into the steaming warm natural sulphur spring bath; breathe in the crisp rural countryside air.",
        "odia_phrase": "Bhai, Atri ushna prasrabana rasta kouthi? (Brother, where is the road to the Atri hot spring?)",
        "screen_off": "Leave notifications behind—unwind your muscles in geothermal mineral waters surrounded by banyan trees."
    },
    "mukteswara": {
        "name": "Mukteswara & Parasurameswara Temples",
        "category": "Heritage & Culture",
        "distance": "5.5 km",
        "focus": "10th-century Kalinga torana archway, peaceful ancient pond paths, carved stone courtyards",
        "sensory_challenge": "Trace your fingers over the smooth 10th-century Kalinga torana archway; sit in the shaded stone courtyard listening to temple chimes.",
        "odia_phrase": "Bhai, Mukteswara Mandira kouthi? (Brother, where is the Mukteswara temple?)",
        "screen_off": "Sit quietly on the ancient red sandstone steps next to the Marichi Kunda tank with no phone distractions."
    },
    "tribal": {
        "name": "Museum of Tribal Arts & Artifacts",
        "category": "Heritage & Culture",
        "distance": "6 km",
        "focus": "Authentic tribal dwellings, lush garden walkways, rich indigenous crafts and heritage",
        "sensory_challenge": "Walk barefoot onto the cool earthen verandas of authentic tribal hut replicas under thick Sal tree canopies.",
        "odia_phrase": "Eithi Tribal Museum gate kouthi? (Where is the Tribal Museum gate?)",
        "screen_off": "Explore 14 authentic tribal dwellings with zero screens—feel the organic mud walls and straw-thatched roofs."
    },
    "kalabhoomi": {
        "name": "Odisha Crafts Museum - Kala Bhoomi",
        "category": "Heritage & Culture",
        "distance": "2.2 km",
        "focus": "12-acre terracotta courtyards, live artisan workshops, peaceful outdoor open-air galleries",
        "sensory_challenge": "Listen to the steady tap-tap of stone carvers in open courtyards; admire terracotta brick textures under open skies.",
        "odia_phrase": "Kala Bhoomi entry ticket kete tanka? (How much is the Kala Bhoomi entry ticket?)",
        "screen_off": "Stroll through 12 acres of terracotta courtyards and lily ponds—pocket your phone and observe master artisans at work."
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
    origin_campus_name: str,
    student_state: str,
    hour: int,
    comfort_data: dict,
    transit_info: str
) -> str:
    """Zero-latency offline fallback pocket guide strictly under 160 words."""
    advisory = comfort_data.get("advisory", "Safe weather window.")
    comfort = comfort_data.get("comfort_class", "Optimal")

    guide = f"""1. Transit from {origin_campus_name}: {transit_info}.
2. Sensory Touch-Grass: {preset['sensory_challenge']} [{comfort} weather: {advisory}]
3. Odia Phrase: "{preset['odia_phrase']}"
4. Screen-Off Protocol: {preset['screen_off']}"""

    return _enforce_word_limit(guide, max_words=160)


def generate_pocket_guide(
    destination_id: str,
    origin_campus: str = "iter",
    student_state: str = "Hosteller",
    hour: int = 7,
    comfort_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a pocket guide strictly under 160 words targeted at university hostellers in Bhubaneswar.
    1. Tries Groq Cloud models in sequence.
    2. Falls back to Google Gemini (gemini-2.5-flash).
    3. Falls back to zero-latency deterministic generator.
    """
    dest_key = destination_id.lower().strip()
    preset = TRAIL_PRESETS.get(dest_key, TRAIL_PRESETS["khandagiri"])
    campus_info = CAMPUS_HUBS.get(origin_campus.lower().strip(), CAMPUS_HUBS["iter"])
    origin_name = campus_info["short_name"]

    # Pull transit instruction for this specific campus-destination pair
    dest_meta = DESTINATIONS_DATA.get(dest_key, DESTINATIONS_DATA["khandagiri"])
    transit_route = dest_meta.get("bus_routes", {}).get(campus_info["id"], "Mo Bus / shared auto corridor")

    if comfort_data is None:
        comfort_data = {
            "comfort_class": "Optimal",
            "is_outdoor_safe": True,
            "advisory": "Pleasant morning coastal breeze."
        }

    comfort_class = comfort_data.get("comfort_class", "Optimal")
    advisory = comfort_data.get("advisory", "Safe trail conditions.")

    preset_dist = preset.get("distance", "Bhubaneswar")
    preset_focus = preset.get("focus", preset.get("name", "Outdoor Escape"))
    prompt = f"""You are the PravasiTrail field scout for a college hosteller from {student_state} studying at {campus_info['name']} in Bhubaneswar.
Generate a high-impact pocket field card for {preset['name']} ({preset_dist}, {preset_focus}) departing {origin_name} campus at {hour:02d}:00.
Weather Comfort: {comfort_class} ({advisory}).
Campus Transit Corridor: {transit_route}.

Provide EXACTLY these 4 numbered items. Keep total response strictly under 140 words.
1. Transit from {origin_name}: Specific transit corridor ({transit_route}), board stop, and student fare in ₹.
2. Sensory Touch-Grass Challenge: Physical sensation to experience (e.g., touch sandstone, feel reservoir mist, river sandbar).
3. Essential Odia Driver Phrase: Conversational phrase for auto/bus conductor with English pronunciation and meaning.
4. Screen-Off Protocol: A punchy one-sentence rule telling the student to put the phone in their pocket.
No conversational intro or outro."""

    # 1. Try Groq Cloud models
    models_to_try = getattr(config, "PRIMARY_MODELS", [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "allam-2-7b"
    ])

    if groq_client:
        for model in models_to_try:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a concise offline field scout guide for Bhubaneswar students. Never exceed 140 words."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4,
                    max_tokens=220
                )
                raw_text = response.choices[0].message.content.strip()
                if raw_text:
                    logger.info(f"Generated pocket guide using Groq ({model}).")
                    return _enforce_word_limit(raw_text, max_words=160)
            except Exception as err:
                logger.warning(f"Groq model '{model}' failed ({err}). Trying next...")
                continue

    # 2. Try Google Gemini
    if genai and config.GEMINI_API_KEY:
        gemini_models_to_try = getattr(config, "GEMINI_FALLBACK_MODELS", ["gemini-2.5-flash", "gemini-flash-latest"])
        for g_model_name in gemini_models_to_try:
            try:
                g_model = genai.GenerativeModel(g_model_name)
                gemini_resp = g_model.generate_content(
                    f"You are a concise offline field scout guide for Bhubaneswar students. Never exceed 140 words.\n\n{prompt}"
                )
                raw_text = gemini_resp.text.strip()
                if raw_text:
                    logger.info(f"Generated pocket guide using Google Gemini ({g_model_name}).")
                    return _enforce_word_limit(raw_text, max_words=160)
            except Exception as gemini_err:
                logger.warning(f"Gemini model '{g_model_name}' failed ({gemini_err}). Trying next...")
                continue

    # 3. Fallback to high-quality deterministic response guaranteed under 160 words
    logger.info("Using deterministic offline trail scout engine.")
    return _build_deterministic_guide(
        dest_key=dest_key,
        preset=preset,
        origin_campus_name=origin_name,
        student_state=student_state,
        hour=hour,
        comfort_data=comfort_data,
        transit_info=transit_route
    )


# Backward-compatible wrapper for router and full-itinerary integration
class LLMTrailScoutService:
    def get_all_trails(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": k,
                "name": v["name"],
                "category": v.get("category", "General"),
                "distance": v["distance"],
                "focus": v["focus"],
                "highlights": [v["focus"], v["sensory_challenge"]],
                "grass_score": 92
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
                "context_tip": "Standard auto fare shared seat."
            },
            {
                "category": "Street Food & Snacks",
                "odia_script": "ଭାଇ, ଗୋଟେ ପ୍ଲେଟ୍ ଦହିବରା ଆଳୁଦମ୍ ଦିଅନ୍ତୁ।",
                "english_phonetic": "Bhai, gote plate Dahibara Aloodum diantu.",
                "meaning": "Brother, give one plate Dahibara Aloodum.",
                "context_tip": "Iconic Cuttack-Bhubaneswar street food outside heritage gates."
            }
        ]


llm_service = LLMTrailScoutService()


# Quick Heuristic Phrase Fallback for Student Survival
STUDENT_PHRASE_FALLBACKS = [
    {
        "keywords": ["khandagiri", "cave", "caves"],
        "en": "Will you go to Khandagiri caves? How much fare?",
        "or": "ଭାଇ, ଖଣ୍ଡଗିରି ଗୁମ୍ଫା ଯିବେ କି? କେତେ ଟଙ୍କା?",
        "phonetic": "Bhai, Khandagiri gumpha jibe ki? Kete tonka?",
        "tip": "Always address auto drivers as 'Bhai' to receive local student fares."
    },
    {
        "keywords": ["how much", "fare", "price", "rate", "cost", "tanka"],
        "en": "How much will the fare be?",
        "or": "କେତେ ଟଙ୍କା ହେବ?",
        "phonetic": "Kete tonka heba?",
        "tip": "Ask 'Kete tonka heba?' before sitting in the auto to prevent surprise fares."
    },
    {
        "keywords": ["stop", "here", "drop", "rokhantu", "eithi"],
        "en": "Please stop here, brother.",
        "or": "ଏଇଠି ରଖନ୍ତୁ ଭାଇ।",
        "phonetic": "Eithi rokhantu bhai.",
        "tip": "Say this 20 meters before your college gate or trail entrance."
    },
    {
        "keywords": ["dahibara", "aloo", "dum", "food", "eat", "snack"],
        "en": "Please give one plate of Dahibara Aloo Dum.",
        "or": "ଦହିବରା ଆଳୁଦମ୍ ଗୋଟେ ପ୍ଲେଟ୍ ଦିଅନ୍ତୁ।",
        "phonetic": "Dahibara Aloo Dum gote plate diantu.",
        "tip": "Odisha's favorite street snack! Always ask for free spicy 'Dahi Paani' at the end."
    },
    {
        "keywords": ["water", "drink", "thirsty", "paani"],
        "en": "Can I get some drinking water?",
        "or": "ଟିକେ ପାଣି ମିଳିବ କି?",
        "phonetic": "Tike paani milibo ki?",
        "tip": "Keep yourself hydrated during warm afternoon climbs."
    },
    {
        "keywords": ["bus", "mobus", "stop", "station"],
        "en": "Where is the nearest Mo Bus stop?",
        "or": "ପାଖ ମୋ ବସ୍ ଷ୍ଟପ୍ କୋଉଠି ଅଛି?",
        "phonetic": "Pakha Mo Bus stop kouthi achi?",
        "tip": "Mo Buses stop at dedicated blue CRUT bays along all major avenues."
    },
    {
        "keywords": ["iter", "college", "soa", "university"],
        "en": "My college is at ITER Jagamara.",
        "or": "ମୋ କଲେଜ ଆଇଟିଇଆର୍ (ITER) ଜଗମରା ରେ ଅଛି।",
        "phonetic": "Mo college ITER Jagamara re achi.",
        "tip": "Specify 'Jagamara Gate 1' so shared autos drop you right outside."
    },
    {
        "keywords": ["kiit", "patia"],
        "en": "Please drop me at KIIT Square in Patia.",
        "or": "ମୋତେ ପଟିଆ କିଟ୍ ଛକରେ ଓହ୍ଲାଇ ଦିଅନ୍ତୁ।",
        "phonetic": "Mote Patia KIIT Chhak re olhai diantu.",
        "tip": "KIIT square has continuous shared auto queues running down the Infocity road."
    },
    {
        "keywords": ["thank", "thanks", "dhanyabad"],
        "en": "Thank you very much!",
        "or": "ଅଶେଷ ଧନ୍ୟବାଦ!",
        "phonetic": "Ashesha Dhanyabad!",
        "tip": "Politeness earns immense warmth and respect across Odisha."
    }
]


def translate_text(text: str, direction: str = "en-to-or") -> Dict[str, Any]:
    """
    Bidirectional English ⇄ Odia AI translation service powered by Google Gemini (gemini-2.5-flash),
    with Groq failover and instant student survival heuristics.
    """
    clean_text = text.strip()
    if not clean_text:
        return {
            "status": "error",
            "message": "Input text cannot be empty."
        }

    dir_norm = "or-to-en" if direction in ["or-to-en", "odia-to-en", "odia-to-english"] else "en-to-or"
    source_lang = "Odia" if dir_norm == "or-to-en" else "English"
    target_lang = "English" if dir_norm == "or-to-en" else "Odia"

    prompt = f"""You are an expert bidirectional English and Odia conversational translator specialized for out-of-state college students in Bhubaneswar, Odisha.
Task: Translate this {source_lang} text to {target_lang}.
Input text: "{clean_text}"

Return STRICTLY valid JSON with no markdown formatting and no extra commentary:
{{
  "translated_text": "...",
  "phonetic": "...",
  "cultural_tip": "..."
}}
Guidelines:
- translated_text: Accurate, natural translation into {target_lang} (use proper Oriya script if translating to Odia).
- phonetic: English alphabetical pronunciation guide (e.g. 'Bhai, kete tanka heba?') so a student from Bihar, Jharkhand, or UP can pronounce it effortlessly.
- cultural_tip: 1 practical, polite tip for communicating with local auto drivers, bus conductors, street vendors, or college seniors in Bhubaneswar.
"""

    import json, re

    # 1. Try Gemini Flash
    if genai and config.GEMINI_API_KEY:
        gemini_models_to_try = getattr(config, "GEMINI_FALLBACK_MODELS", ["gemini-2.5-flash", "gemini-flash-latest"])
        for g_model_name in gemini_models_to_try:
            try:
                g_model = genai.GenerativeModel(g_model_name)
                gemini_resp = g_model.generate_content(prompt)
                raw_json = gemini_resp.text.strip()
                # Clean possible markdown block
                raw_json = re.sub(r"^```json\s*", "", raw_json, flags=re.MULTILINE)
                raw_json = re.sub(r"^```\s*", "", raw_json, flags=re.MULTILINE)
                raw_json = re.sub(r"```$", "", raw_json, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                c_tip = parsed.get("cultural_tip", "Speak with a friendly tone and address locals as 'Bhai' or 'Mousa'.")
                return {
                    "status": "success",
                    "original_text": clean_text,
                    "direction": dir_norm,
                    "translated_text": parsed.get("translated_text", ""),
                    "phonetic": parsed.get("phonetic", ""),
                    "cultural_tip": c_tip,
                    "tip": c_tip,
                    "meaning": clean_text,
                    "engine": f"Gemini ({g_model_name})",
                    "service": f"Gemini ({g_model_name})"
                }
            except Exception as gem_err:
                logger.warning(f"Gemini translation failed with {g_model_name} ({gem_err}). Trying next...")

    # 2. Try Groq Cloud
    if groq_client:
        groq_models = getattr(config, "PRIMARY_MODELS", ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"])
        for g_model in groq_models:
            try:
                chat_resp = groq_client.chat.completions.create(
                    model=g_model,
                    messages=[
                        {"role": "system", "content": "You are a bilingual English-Odia translator. Return ONLY valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                raw_json = chat_resp.choices[0].message.content.strip()
                raw_json = re.sub(r"^```json\s*", "", raw_json, flags=re.MULTILINE)
                raw_json = re.sub(r"^```\s*", "", raw_json, flags=re.MULTILINE)
                raw_json = re.sub(r"```$", "", raw_json, flags=re.MULTILINE).strip()
                parsed = json.loads(raw_json)
                c_tip = parsed.get("cultural_tip", "Address local drivers respectfully for best student rates.")
                return {
                    "status": "success",
                    "original_text": clean_text,
                    "direction": dir_norm,
                    "translated_text": parsed.get("translated_text", ""),
                    "phonetic": parsed.get("phonetic", ""),
                    "cultural_tip": c_tip,
                    "tip": c_tip,
                    "meaning": clean_text,
                    "engine": f"Groq ({g_model})",
                    "service": f"Groq ({g_model})"
                }
            except Exception as groq_err:
                logger.warning(f"Groq translation failed with {g_model}: {groq_err}")

    # 3. Intelligent Heuristic Match
    low_text = clean_text.lower()
    for item in STUDENT_PHRASE_FALLBACKS:
        if any(kw in low_text for kw in item["keywords"]):
            if dir_norm == "en-to-or":
                return {
                    "status": "success",
                    "original_text": clean_text,
                    "direction": dir_norm,
                    "translated_text": item["or"],
                    "phonetic": item["phonetic"],
                    "cultural_tip": item["tip"],
                    "tip": item["tip"],
                    "meaning": clean_text,
                    "engine": "PravasiTrail Local Student Engine",
                    "service": "PravasiTrail Local Student Engine"
                }
            else:
                return {
                    "status": "success",
                    "original_text": clean_text,
                    "direction": dir_norm,
                    "translated_text": item["en"],
                    "phonetic": item["phonetic"],
                    "cultural_tip": item["tip"],
                    "tip": item["tip"],
                    "meaning": clean_text,
                    "engine": "PravasiTrail Local Student Engine",
                    "service": "PravasiTrail Local Student Engine"
                }

    # Generic Fallback
    if dir_norm == "en-to-or":
        return {
            "status": "success",
            "original_text": clean_text,
            "direction": dir_norm,
            "translated_text": f"ନମସ୍କାର, {clean_text}",
            "phonetic": f"Namaskar, {clean_text}",
            "cultural_tip": "When in doubt, start with 'Namaskar Bhai'—it is universally respected across Odisha.",
            "tip": "When in doubt, start with 'Namaskar Bhai'—it is universally respected across Odisha.",
            "meaning": clean_text,
            "engine": "PravasiTrail Offline Engine",
            "service": "PravasiTrail Offline Engine"
        }
    else:
        return {
            "status": "success",
            "original_text": clean_text,
            "direction": dir_norm,
            "translated_text": clean_text,
            "phonetic": clean_text,
            "cultural_tip": "Spoken Odia is straightforward; focus on root keywords like 'kete' (how much) and 'jibe' (will go).",
            "tip": "Spoken Odia is straightforward; focus on root keywords like 'kete' (how much) and 'jibe' (will go).",
            "meaning": clean_text,
            "engine": "PravasiTrail Offline Engine",
            "service": "PravasiTrail Offline Engine"
        }

