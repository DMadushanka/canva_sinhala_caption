from typing import List, Dict, Any
from datetime import timedelta
import srt

class CaptionFormatter:
    @staticmethod
    def chunk_words_to_segments(words: List[Dict[str, Any]], words_per_chunk: int = 5) -> List[Dict[str, Any]]:
        """
        Groups continuous word-level timestamps into readable subtitle segments.
        Considers pauses (>0.7s) between words to split sentences naturally.
        """
        if not words:
            return []

        segments: List[Dict[str, Any]] = []
        current_words: List[Dict[str, Any]] = []

        for i, w in enumerate(words):
            current_words.append(w)
            
            # Check pause to next word
            is_pause = False
            if i < len(words) - 1:
                next_start = words[i + 1]["start"]
                if next_start - w["end"] > 0.65:
                    is_pause = True

            # If chunk limit reached, or natural pause detected, or end of words
            if len(current_words) >= words_per_chunk or is_pause or i == len(words) - 1:
                seg_text = " ".join([cw["word"] for cw in current_words])
                start_time = current_words[0]["start"]
                end_time = current_words[-1]["end"]

                # Ensure minimum duration of 1.2s for readability unless followed immediately
                if end_time - start_time < 1.0:
                    end_time = start_time + 1.0

                segments.append({
                    "id": len(segments) + 1,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2),
                    "text": seg_text,
                    "words": current_words.copy()
                })
                current_words = []

        return segments

    @staticmethod
    def to_srt(segments: List[Dict[str, Any]]) -> str:
        """
        Generates standard SRT subtitles file content with UTF-8 Sinhala text.
        """
        subtitles = []
        for i, seg in enumerate(segments, start=1):
            start_td = timedelta(seconds=float(seg["start"]))
            end_td = timedelta(seconds=float(seg["end"]))
            subtitles.append(
                srt.Subtitle(
                    index=i,
                    start=start_td,
                    end=end_td,
                    content=seg["text"]
                )
            )
        return srt.compose(subtitles)

    @staticmethod
    def to_vtt(segments: List[Dict[str, Any]]) -> str:
        """
        Generates standard WebVTT subtitles format.
        """
        lines = ["WEBVTT", ""]
        for i, seg in enumerate(segments, start=1):
            start_sec = float(seg["start"])
            end_sec = float(seg["end"])

            def format_vtt_timestamp(seconds: float) -> str:
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = seconds % 60
                return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

            lines.append(f"{i}")
            lines.append(f"{format_vtt_timestamp(start_sec)} --> {format_vtt_timestamp(end_sec)}")
            lines.append(seg["text"])
            lines.append("")

        return "\n".join(lines)
