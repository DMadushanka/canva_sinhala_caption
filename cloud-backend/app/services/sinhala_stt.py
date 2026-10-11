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
        Uses Gemini Audio to generate highly accurate Sinhala captions with natural punctuation,
        numbers, and timestamps formatted directly in structured JSON.
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_api_key)

            # Upload audio file
            audio_file = genai.upload_file(path=audio_wav_path)

            prompt = (
                "You are an expert Sinhala audio transcriptionist. Listen to this audio and produce accurate "
                "Sinhala subtitles. Return a strict JSON array of subtitle segments without markdown ticks or commentary.\n"
                "Format requirement:\n"
                "[\n"
                "  {\"start\": 0.0, \"end\": 2.4, \"text\": \"ආයුබෝවන් සියලු දෙනාටම\", \"words\": [{\"word\": \"ආයුබෝවන්\", \"start\": 0.0, \"end\": 1.1}, {\"word\": \"සියලු\", \"start\": 1.1, \"end\": 1.6}, {\"word\": \"දෙනාටම\", \"start\": 1.6, \"end\": 2.4}]}\n"
                "]\n"
                "Ensure correct Sinhala spelling (අක්ෂර වින්‍යාසය) and natural punctuation."
            )

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([audio_file, prompt])
            
            raw_text = response.text.strip()
            # Clean possible markdown block
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())
            return parsed
        except Exception as e:
            logger.error(f"Gemini Audio STT failed: {e}")
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
