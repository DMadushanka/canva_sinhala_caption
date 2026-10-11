import os
import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class SinhalaSpeechService:
    def __init__(self):
        self.gcp_credentials = settings.GOOGLE_APPLICATION_CREDENTIALS
        self.gemini_api_key = settings.GEMINI_API_KEY

    def transcribe_with_google_cloud(self, audio_wav_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes audio using Google Cloud Speech-to-Text API configured for Sinhala (si-LK).
        Extracts high-precision word-level timestamps.
        """
        try:
            from google.cloud import speech_v1p1beta1 as speech

            client = speech.SpeechClient()

            with open(audio_wav_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="si-LK",
                alternative_language_codes=["en-US"], # Handles mixed Sinhala-English terms
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
                model="default"
            )

            response = client.recognize(config=config, audio=audio)

            words_data: List[Dict[str, Any]] = []
            for result in response.results:
                alternative = result.alternatives[0]
                for word_info in alternative.words:
                    start_sec = word_info.start_time.total_seconds()
                    end_sec = word_info.end_time.total_seconds()
                    word = word_info.word.strip()
                    if word:
                        words_data.append({
                            "word": word,
                            "start": round(start_sec, 3),
                            "end": round(end_sec, 3)
                        })

            return words_data
        except Exception as e:
            logger.error(f"Google Cloud Speech STT failed: {e}")
            raise

    def transcribe_with_gemini(self, audio_wav_path: str) -> List[Dict[str, Any]]:
        """
        Uses Gemini 1.5 Flash Audio API to generate highly accurate Sinhala captions
        with natural punctuation, timestamps, and numbers.
        Uses direct HTTP REST API to ensure 100% compatibility without grpc issues.
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured in .env file.")

        try:
            import base64
            import requests
            import mimetypes

            with open(audio_wav_path, "rb") as f:
                audio_bytes = f.read()

            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            guessed_mime, _ = mimetypes.guess_type(audio_wav_path)
            mime_type = guessed_mime or "audio/wav"

            prompt = (
                "You are an expert Sinhala audio transcriptionist. Listen to this audio carefully and produce "
                "completely accurate Sinhala subtitles (සිංහල උපසිරැසි).\n"
                "Return ONLY a strict JSON array of subtitle segments without any markdown wrapping or explanatory text.\n"
                "JSON format required:\n"
                "[\n"
                "  {\"start\": 0.0, \"end\": 2.5, \"text\": \"ආයුබෝවන් සියලු දෙනාටම\"},\n"
                "  {\"start\": 2.6, \"end\": 5.1, \"text\": \"අද අපි කතා කරන්නේ...\"}\n"
                "]\n"
                "Ensure correct Sinhala spelling, accurate time offsets, and clear punctuation."
            )

            import time

            candidate_models = [
                "gemini-flash-latest",
                "gemini-2.5-flash",
                "gemini-2.5-flash-lite",
                "gemini-flash-lite-latest",
            ]
            resp = None
            last_err = ""

            for model_name in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_api_key}"
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": b64_audio
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "response_mime_type": "application/json"
                    }
                }

                try:
                    logger.info(f"Attempting Sinhala transcription with model {model_name}...")
                    curr_resp = requests.post(url, json=payload, timeout=60)
                    if curr_resp.ok:
                        resp = curr_resp
                        logger.info(f"Successfully transcribed with {model_name}")
                        break
                    else:
                        last_err = f"{curr_resp.status_code} - {curr_resp.text[:120]}"
                        logger.warning(f"Model {model_name} returned {curr_resp.status_code}. Trying next model...")
                except Exception as req_err:
                    last_err = str(req_err)
                    logger.warning(f"Model {model_name} request failed ({req_err}). Trying next model...")


            if resp is None:
                raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")

            result = resp.json()
            candidates = result.get("candidates", [])
            if not candidates:
                raise ValueError("No response generated from Gemini Audio.")

            content_text = candidates[0]["content"]["parts"][0]["text"].strip()
            
            # Clean markdown formatting if present
            if content_text.startswith("```json"):
                content_text = content_text[7:]
            if content_text.startswith("```"):
                content_text = content_text[3:]
            if content_text.endswith("```"):
                content_text = content_text[:-3]

            parsed = json.loads(content_text.strip())
            
            # Ensure items have IDs
            formatted_segments = []
            for idx, item in enumerate(parsed, start=1):
                formatted_segments.append({
                    "id": idx,
                    "start": round(float(item.get("start", 0)), 2),
                    "end": round(float(item.get("end", 0)), 2),
                    "text": item.get("text", "").strip()
                })

            return formatted_segments

        except Exception as e:
            logger.error(f"Gemini Audio STT failed: {e}", exc_info=True)
            raise

    def transcribe(self, audio_wav_path: str, engine: str = "google") -> Dict[str, Any]:
        """
        Main transcription router: supports 'google', 'gemini', or 'auto' (hybrid).
        """
        if engine == "gemini":
            segments = self.transcribe_with_gemini(audio_wav_path)
            return {"engine": "gemini", "segments": segments}
        
        # Default: Google Cloud Speech-to-Text with word-level timestamps
        try:
            words = self.transcribe_with_google_cloud(audio_wav_path)
            return {"engine": "google-cloud-stt", "words": words}
        except Exception as gcp_err:
            logger.warning(f"Google Cloud STT failed ({gcp_err}). Attempting Gemini fallback...")
            if self.gemini_api_key:
                segments = self.transcribe_with_gemini(audio_wav_path)
                return {"engine": "gemini-fallback", "segments": segments}
            raise gcp_err
