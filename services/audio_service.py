import logging
import re
import base64
from typing import Optional, Dict, Any
import httpx
import config

logger = logging.getLogger(__name__)

def clean_markdown_for_speech(text: str) -> str:
    """
    Remove Markdown markup, URLs, emojis, and bullet points for smooth voice narration.
    """
    if not text:
        return ""
    # Remove markdown headers
    clean = re.sub(r"#+\s*", "", text)
    # Remove bold / italics
    clean = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean)
    clean = re.sub(r"\*([^*]+)\*", r"\1", clean)
    clean = re.sub(r"__([^_]+)__", r"\1", clean)
    clean = re.sub(r"_([^_]+)_", r"\1", clean)
    # Remove links [text](url) -> text
    clean = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", clean)
    # Remove URLs
    clean = re.sub(r"https?://\S+", "", clean)
    # Remove bullet symbols
    clean = re.sub(r"^\s*[-*•]\s*", "", clean, flags=re.MULTILINE)
    # Remove extra whitespace
    clean = re.sub(r"\n+", ". ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def generate_elevenlabs_audio(text: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Synthesize speech using ElevenLabs API.
    Returns a dict with audio base64 or fallback instructions.
    """
    clean_text = clean_markdown_for_speech(text)
    if not clean_text:
        return {"status": "error", "message": "No text provided for audio narration."}

    # Truncate text if excessively long to save quota (approx 1200 characters is plenty for a 90-sec pocket guide)
    if len(clean_text) > 1200:
        clean_text = clean_text[:1200] + "..."

    api_key = config.ELEVENLABS_API_KEY
    target_voice = voice_id or config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"

    if not api_key or api_key.strip() == "":
        logger.info("ElevenLabs API key not configured; signalling client-side Web Speech fallback.")
        return {
            "status": "fallback",
            "provider": "browser_speech_synthesis",
            "message": "ElevenLabs API key not set in .env. Using high-fidelity browser voice companion.",
            "clean_text": clean_text
        }

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice}"
    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": clean_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                audio_bytes = resp.content
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                return {
                    "status": "success",
                    "provider": "elevenlabs",
                    "voice_id": target_voice,
                    "audio_url": f"data:audio/mpeg;base64,{b64_audio}",
                    "clean_text": clean_text
                }
            else:
                logger.warning(f"ElevenLabs API returned {resp.status_code}: {resp.text}")
                return {
                    "status": "fallback",
                    "provider": "browser_speech_synthesis",
                    "message": f"ElevenLabs quota or key error (HTTP {resp.status_code}). Falling back to browser speech synthesis.",
                    "clean_text": clean_text
                }
    except Exception as exc:
        logger.error(f"Error calling ElevenLabs API: {exc}")
        return {
            "status": "fallback",
            "provider": "browser_speech_synthesis",
            "message": f"Network exception: {str(exc)}. Falling back to browser speech synthesis.",
            "clean_text": clean_text
        }
