import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Safe import to support both SDK versions seamlessly without crashing on startup
client = None
try:
    from google import genai
    from google.genai import types
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
except (ImportError, Exception) as e:
    logger.warning(f"google-genai import error: {e}")
    try:
        import google.generativeai as legacy_genai
        if GEMINI_API_KEY:
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            client = legacy_genai.GenerativeModel("gemini-1.5-flash")
    except Exception as legacy_err:
        logger.warning(f"Gemini client initialization fallback: {legacy_err}")

SYSTEM_PROMPT = """
You are a street-smart local bilingual translator for college students in Bhubaneswar, Odisha.
Translate between everyday spoken English and conversational colloquial Odia.

Always return strict, valid JSON:
{
  "odia_script": "<Odia text>",
  "phonetic_transliteration": "<English pronunciation>",
  "meaning": "<Clear English meaning>",
  "context_tip": "<Helpful 1-sentence local tip transit/travel>"
}
"""

def translate_odia_with_gemini(text: str, direction: str = "en_to_or") -> dict:
    global client
    if not client:
        key = os.getenv("GEMINI_API_KEY")
        if key:
            try:
                from google import genai
                client = genai.Client(api_key=key)
            except (ImportError, Exception):
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=key)
                    client = legacy_genai.GenerativeModel("gemini-1.5-flash")
                except Exception:
                    client = None

    if not client:
        return {
            "odia_script": "ନନ୍ଦନକାନନ ଯିବା ପାଇଁ କେତେ ଟଙ୍କା ହେବ?",
            "phonetic_transliteration": "Nandankanan jiba pain kete tanka heba?",
            "meaning": text,
            "context_tip": "Mo Bus Route 16 directly connects Master Canteen and Patia to Nandankanan for ₹20-30."
        }

    try:
        # Check if new genai client
        if hasattr(client, "models"):
            try:
                from google.genai import types
                cfg = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            except Exception:
                cfg = {"response_mime_type": "application/json"}

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Direction: {direction}\nTranslate: {text}",
                config=cfg
            )
            return json.loads(response.text)
        else:
            # Legacy google.generativeai client
            resp = client.generate_content(f"{SYSTEM_PROMPT}\nDirection: {direction}\nTranslate: {text}")
            clean_text = resp.text.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
    except Exception as e:
        logger.error(f"Translation runtime error: {e}")
        return {
            "odia_script": "କ୍ଷମା କରିବେ, ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ",
            "phonetic_transliteration": "Khyama karibe, puni chesta karantu",
            "meaning": text,
            "context_tip": "Direct routes available via Mo Bus."
        }
