export interface WordItem {
  word: string;
  start: number;
  end: number;
}

export interface SubtitleSegment {
  id: number;
  start: number;
  end: number;
  text: string;
  words?: WordItem[];
}

export interface TranscriptionResponse {
  success: boolean;
  engine_used: string;
  segment_count: number;
  segments: SubtitleSegment[];
  srt: string;
  vtt: string;
}

export interface CaptionStyle {
  preset: "bold_glow" | "classic_subtitle" | "karaoke_box" | "cinematic";
  fontFamily: string;
  fontSize: number;
  textColor: string;
  strokeColor: string;
  backgroundColor: string;
  position: "bottom" | "center" | "top";
}
