import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Canva Sinhala Caption API"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://www.canva.com,https://canva.com"
    GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MAX_AUDIO_SIZE_MB: int = 100
    DEFAULT_CHUNK_WORDS: int = 5

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
