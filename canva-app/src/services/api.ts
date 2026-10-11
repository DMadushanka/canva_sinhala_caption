import { SubtitleSegment, TranscriptionResponse } from "../types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8080";

export async function transcribeMedia(
  file: File,
  engine: "google" | "gemini" = "google",
  wordsPerChunk: number = 5
): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("engine", engine);
  formData.append("words_per_chunk", wordsPerChunk.toString());

  const res = await fetch(`${BACKEND_URL}/api/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Transcription failed with HTTP status ${res.status}`);
  }

  return await res.json();
}

export function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
