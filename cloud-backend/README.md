# Canva Sinhala Caption Cloud Backend

A production-ready FastAPI service providing automated Sinhala (සිංහල) Speech-to-Text transcription with word-level timestamps and subtitle formatting for Canva video editing.

## Features
- **Accurate Sinhala Speech Recognition**:
  - Google Cloud Speech-to-Text (`si-LK`) with millisecond word timestamps.
  - Gemini Audio integration for contextual spelling and colloquial speech.
- **Audio Preprocessing**: FFmpeg automatic 16kHz mono PCM normalization from video (`mp4`, `webm`, `mov`) and audio files.
- **Sinhala Formatting**: Smart punctuation, word grouping (configurable chunk size), and pause-aware subtitle splitting.
- **Export Standards**: Generates `.srt` and `.vtt` formats with UTF-8 Sinhala encoding.

## Setup & Running Locally

### 1. Requirements
- Python 3.10+
- FFmpeg installed on your machine (`choco install ffmpeg` on Windows, `brew install ffmpeg` on Mac, or `apt install ffmpeg` on Ubuntu).

### 2. Install Dependencies
```bash
cd cloud-backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your:
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud service account JSON file (with Speech-to-Text API enabled).
- `GEMINI_API_KEY`: Your Google AI Studio API key (optional fallback / contextual corrector).

### 4. Run Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
API documentation is available at `http://localhost:8080/docs`.

## Cloud Deployment (Google Cloud Run / AWS ECS)

Build and deploy the Docker container:
```bash
docker build -t canva-sinhala-caption-backend .
docker run -p 8080:8080 --env-file .env canva-sinhala-caption-backend
```
