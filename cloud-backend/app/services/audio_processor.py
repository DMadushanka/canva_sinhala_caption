import os
import subprocess
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioProcessor:
    @staticmethod
    def extract_and_normalize(input_path: str, output_path: str = None) -> str:
        """
        Converts any media (video or audio) into standardized 16kHz mono 16-bit PCM WAV,
        which provides the highest accuracy for Sinhala Speech-to-Text models.
        """
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = tmp.name
            tmp.close()

        # Locate FFmpeg binary (bundled via imageio-ffmpeg or system PATH)
        ffmpeg_bin = "ffmpeg"
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass

        cmd = [
            ffmpeg_bin,
            "-y",                   # Overwrite output
            "-i", input_path,       # Input file
            "-vn",                  # Disable video stream
            "-acodec", "pcm_s16le", # PCM 16-bit little-endian
            "-ar", "16000",         # Sample rate 16kHz
            "-ac", "1",             # Mono audio
            output_path
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path
        except Exception as e:
            logger.warning(f"FFmpeg extraction failed ({e}). Returning original media path as fallback.")
            return input_path

    @staticmethod
    def cleanup_file(file_path: str):
        """Safely removes temporary files."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {file_path}: {e}")
