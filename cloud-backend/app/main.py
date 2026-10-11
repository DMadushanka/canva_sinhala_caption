import os
import tempfile
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.services.audio_processor import AudioProcessor
from app.services.sinhala_stt import SinhalaSpeechService
from app.services.caption_formatter import CaptionFormatter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Cloud Speech-to-Text backend for Canva Sinhala Video Captions"
)

# CORS configuration to allow requests from Canva editor & localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def add_private_network_headers(request, call_next):
    """
    Chrome Private Network Access support: Allows https://www.canva.com
    to communicate with local development servers.
    """
    origin = request.headers.get("origin", "*")
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    response.headers["Access-Control-Allow-Origin"] = origin
    return response

stt_service = SinhalaSpeechService()

class WordItem(BaseModel):
    word: str
    start: float
    end: float

class SubtitleSegment(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: Optional[List[WordItem]] = None

class ExportRequest(BaseModel):
    segments: List[SubtitleSegment]

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "supported_language": "Sinhala (si-LK)",
        "gcp_configured": bool(settings.GOOGLE_APPLICATION_CREDENTIALS),
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

latest_captions = {
    "vtt": "",
    "srt": ""
}

@app.post("/api/transcribe")
async def transcribe_media(
    file: UploadFile = File(...),
    engine: str = Form(default="google"),
    words_per_chunk: int = Form(default=5)
):
    """
    Accepts video or audio file, extracts audio, transcribes to Sinhala with high accuracy,
    and returns timed segments along with ready-to-use SRT and VTT captions.
    """
    temp_in = None
    temp_wav = None

    try:
        suffix = os.path.splitext(file.filename or "")[1] or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            temp_in = f.name
            content = await file.read()
            f.write(content)

        logger.info(f"Processing media file: {file.filename} ({len(content)} bytes)")

        # 1. Extract & normalize to 16kHz mono WAV
        temp_wav = AudioProcessor.extract_and_normalize(temp_in)

        # 2. Sinhala Speech Recognition
        stt_result = stt_service.transcribe(temp_wav, engine=engine)

        # 3. Format into subtitle segments
        if "words" in stt_result:
            segments = CaptionFormatter.chunk_words_to_segments(
                stt_result["words"],
                words_per_chunk=words_per_chunk
            )
        elif "segments" in stt_result:
            segments = stt_result["segments"]
        else:
            segments = []
        # 4. Generate SRT and VTT representations
        srt_content = CaptionFormatter.to_srt(segments)
        vtt_content = CaptionFormatter.to_vtt(segments)

        latest_captions["srt"] = srt_content
        latest_captions["vtt"] = vtt_content

        return {
            "success": True,
            "engine_used": stt_result.get("engine", engine),
            "segment_count": len(segments),
            "segments": segments,
            "srt": srt_content,
            "vtt": vtt_content
        }

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        AudioProcessor.cleanup_file(temp_in)
        AudioProcessor.cleanup_file(temp_wav)

class PrepareDownloadRequest(BaseModel):
    vtt: Optional[str] = None
    srt: Optional[str] = None
    segments: Optional[List[SubtitleSegment]] = None

@app.post("/api/prepare-download")
def prepare_download(payload: PrepareDownloadRequest):
    """Saves the current subtitles into memory so direct browser GET download can fetch it."""
    if payload.segments:
        payload_segments = [seg.dict() for seg in payload.segments]
        latest_captions["vtt"] = CaptionFormatter.to_vtt(payload_segments)
        latest_captions["srt"] = CaptionFormatter.to_srt(payload_segments)
    if payload.vtt:
        latest_captions["vtt"] = payload.vtt
    if payload.srt:
        latest_captions["srt"] = payload.srt
    return {
        "ok": True,
        "vtt_url": "/api/download/vtt",
        "srt_url": "/api/download/srt"
    }

@app.get("/api/download/vtt")
def download_vtt():
    """Direct browser GET download for sinhala_captions.vtt file."""
    vtt_text = latest_captions.get("vtt", "")
    if not vtt_text:
        vtt_text = "WEBVTT\n\n1\n00:00:00.000 --> 00:00:05.000\n(No subtitles generated yet)\n"
    return Response(
        content=vtt_text.encode("utf-8"),
        media_type="text/vtt",
        headers={
            "Content-Disposition": 'attachment; filename="sinhala_captions.vtt"',
            "Content-Type": "text/vtt; charset=utf-8",
            "Cache-Control": "no-cache",
        }
    )

@app.get("/api/download/srt")
def download_srt():
    """Direct browser GET download for sinhala_captions.srt file."""
    srt_text = latest_captions.get("srt", "")
    if not srt_text:
        srt_text = "1\n00:00:00,000 --> 00:00:05,000\n(No subtitles generated yet)\n"
    return Response(
        content=srt_text.encode("utf-8"),
        media_type="application/x-subrip",
        headers={
            "Content-Disposition": 'attachment; filename="sinhala_captions.srt"',
            "Content-Type": "text/plain; charset=utf-8",
            "Cache-Control": "no-cache",
        }
    )

@app.post("/api/export-srt")
def export_srt(payload: ExportRequest):
    """Generates downloadable UTF-8 .srt file from segments."""
    srt_text = CaptionFormatter.to_srt([seg.dict() for seg in payload.segments])
    return Response(
        content=srt_text.encode("utf-8"),
        media_type="application/x-subrip",
        headers={"Content-Disposition": 'attachment; filename="sinhala_captions.srt"'}
    )

@app.post("/api/export-vtt")
def export_vtt(payload: ExportRequest):
    """Generates downloadable UTF-8 .vtt file from segments."""
    vtt_text = CaptionFormatter.to_vtt([seg.dict() for seg in payload.segments])
    return Response(
        content=vtt_text.encode("utf-8"),
        media_type="text/vtt",
        headers={"Content-Disposition": 'attachment; filename="sinhala_captions.vtt"'}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

