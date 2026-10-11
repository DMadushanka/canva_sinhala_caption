FROM python:3.11-slim

# Install system dependencies including FFmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose port
EXPOSE 8080

ENV PORT=8080
ENV HOST=0.0.0.0

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
