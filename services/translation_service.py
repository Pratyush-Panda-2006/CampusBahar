import os
import json
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

SYSTEM_INSTRUCTION = """
You are an expert bilingual interpreter and cultural guide specializing in everyday colloquial Odia as spoken in Bhubaneswar, Cuttack, and Khordha, India.
Your mission is to help non-Odia university students communicate naturally with local auto drivers, Mo Bus conductors, street vendors, and locals.

Rules:
1. Spoken Street Odia: Provide natural conversational Odia, NOT stiff, formal, or textbook Odia.
2. Resolve phonetic typos automatically:
   - "nandankanand" -> "Nandankanan"
   - "khandgiri" -> "Khandagiri"
   - "lingraj" -> "Lingaraj"
   - "jagmara" -> "Jagamara"
3. For pricing/transit questions (e.g., "how much for X"):
   - Phrasing: "[Destination] jiba pain kete tanka heba?" or "[Destination] jibe ki? Kete heba?".
4. Always return strictly valid JSON matching this schema:
{
  "odia_script": "ନନ୍ଦନକାନନ ଯିବା ପାଇଁ କେତେ ଟଙ୍କା ହେବ?",
  "phonetic_transliteration": "Nandankanan jiba pain kete tanka heba?",
  "meaning": "How much fare to go to Nandankanan?",
  "context_tip": "Mo Bus Route 16 goes directly to Nandankanan from Master Canteen and Patia for ₹20-30."
}
"""

def translate_odia_with_gemini(text: str, direction: str = "en_to_or") -> dict:
    global client
    if not client:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            client = genai.Client(api_key=gemini_key)

    if not client:
        return {
            "odia_script": "ନନ୍ଦନକାନନ ଯିବା ପାଇଁ କେତେ ଟଙ୍କା ହେବ?",
            "phonetic_transliteration": "Nandankanan jiba pain kete tanka heba?",
            "meaning": text,
            "context_tip": "GEMINI_API_KEY is missing in your .env file."
        }

    user_prompt = f"Direction: {direction}\nUser input text: \"{text}\""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                temperature=0.2,
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini translation error: {e}")
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0.2,
                )
            )
            return json.loads(response.text)
        except Exception:
            pass

        return {
            "odia_script": "ନନ୍ଦନକାନନ ଯିବା ପାଇଁ କେତେ ଟଙ୍କା ହେବ?",
            "phonetic_transliteration": "Nandankanan jiba pain kete tanka heba?",
            "meaning": text,
            "context_tip": "Mo Bus Route 16 directly connects to Nandankanan from Master Canteen."
        }
