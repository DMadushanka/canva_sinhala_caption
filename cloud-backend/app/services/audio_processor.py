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

        # Try FFmpeg command line first
        cmd = [
            "ffmpeg",
            "-y",                   # Overwrite output
            "-i", input_path,       # Input file
            "-vn",                  # Disable video
            "-acodec", "pcm_s16le", # PCM 16-bit little-endian
            "-ar", "16000",         # Sample rate 16kHz
            "-ac", "1",             # Mono audio
            output_path
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.warning(f"FFmpeg failed or not found: {e}. Trying pydub fallback.")
            try:
                from pydub import AudioSegment
                sound = AudioSegment.from_file(input_path)
                sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                sound.export(output_path, format="wav")
                return output_path
            except Exception as pydub_err:
                logger.error(f"Failed to process audio with pydub: {pydub_err}")
                raise RuntimeError(f"Audio processing failed. Ensure FFmpeg is installed: {pydub_err}")

    @staticmethod
    def cleanup_file(file_path: str):
        """Safely removes temporary files."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {file_path}: {e}")
