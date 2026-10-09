import os
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


async def synthesize_elevenlabs_audio_bytes(text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
    """
    Synthesize audio using ElevenLabs API (httpx.AsyncClient).
    Uses primary voice Rachel (21m00Tcm4TlvDq8ikWAM) with model eleven_turbo_v2_5,
    falling back to premade Sarah (EXAVITQu4vr4xnSDxMaL) if free-tier payment restriction occurs.
    Returns raw MP3 bytes or None.
    """
    clean_text = clean_markdown_for_speech(text)
    if not clean_text:
        return None

    if len(clean_text) > 1200:
        clean_text = clean_text[:1200] + "..."

    api_key = os.getenv("ELEVENLABS_API_KEY") or config.ELEVENLABS_API_KEY
    if not api_key or api_key.strip() == "":
        logger.info("ElevenLabs API key not configured.")
        return None

    primary_voice = voice_id or config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
    fallback_voice = "EXAVITQu4vr4xnSDxMaL"
    voices_to_try = [primary_voice]
    if primary_voice != fallback_voice:
        voices_to_try.append(fallback_voice)

    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        for vid in voices_to_try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}"
            payload = {
                "text": clean_text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    logger.info(f"ElevenLabs audio generated successfully using voice {vid}.")
                    return resp.content
                logger.warning(f"ElevenLabs voice {vid} returned HTTP {resp.status_code}: {resp.text}")
            except Exception as exc:
                logger.error(f"Error calling ElevenLabs API for {vid}: {exc}")

    return None


def generate_elevenlabs_audio(text: str, voice_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Synchronous helper returning base64 data URL dict for backwards compatibility.
    """
    clean_text = clean_markdown_for_speech(text)
    if not clean_text:
        return {"status": "error", "message": "No text provided for audio narration."}

    api_key = os.getenv("ELEVENLABS_API_KEY") or config.ELEVENLABS_API_KEY
    if not api_key or api_key.strip() == "":
        return {
            "status": "fallback",
            "provider": "browser_speech_synthesis",
            "message": "ElevenLabs API key not configured. Using browser speech synthesis.",
            "clean_text": clean_text
        }

    target_voice = voice_id or config.ELEVENLABS_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{target_voice}"
    headers = {
        "xi-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": clean_text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code != 200 and resp.status_code == 402:
                # Try premade fallback voice
                url = f"https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"
                resp = client.post(url, json=payload, headers=headers)
                target_voice = "EXAVITQu4vr4xnSDxMaL"

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
    except Exception as exc:
        logger.error(f"Error in generate_elevenlabs_audio: {exc}")

    return {
        "status": "fallback",
        "provider": "browser_speech_synthesis",
        "message": "Falling back to browser speech synthesis.",
        "clean_text": clean_text
    }
