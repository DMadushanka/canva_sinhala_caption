import { TranscriptionResponse } from "../types";

export function getBackendUrl(): string {
  return localStorage.getItem("canva_sinhala_backend_url") || (import.meta as any).env?.VITE_BACKEND_URL || "http://localhost:8000";
}

export function setBackendUrl(url: string): void {
  localStorage.setItem("canva_sinhala_backend_url", url);
}

export async function checkBackendHealth(): Promise<{ ok: boolean; message: string }> {
  const url = getBackendUrl();
  try {
    const res = await fetch(`${url}/`, {
      method: "GET",
      headers: { "Bypass-Tunnel-Reminder": "true" },
    });
    if (res.ok) {
      const data = await res.json();
      return { ok: true, message: `Connected (${data.service || "Online"})` };
    }
    return { ok: false, message: `Server responded with status ${res.status}` };
  } catch (err: any) {
    return { ok: false, message: `Cannot reach backend at ${url}` };
  }
}

export async function transcribeMedia(
  file: File,
  engine: "google" | "gemini" = "google",
  wordsPerChunk: number = 5
): Promise<TranscriptionResponse> {
  const backendUrl = getBackendUrl();
  const formData = new FormData();
  formData.append("file", file);
  formData.append("engine", engine);
  formData.append("words_per_chunk", wordsPerChunk.toString());

  try {
    const res = await fetch(`${backendUrl}/api/transcribe`, {
      method: "POST",
      headers: { "Bypass-Tunnel-Reminder": "true" },
      body: formData,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error (HTTP ${res.status})`);
    }

    return await res.json();
  } catch (err: any) {
    if (err.message && err.message.includes("Failed to fetch")) {
      throw new Error(
        `Cloud Backend එකට සම්බන්ධ විය නොහැකි විය (${backendUrl}). කරුණාකර Python backend එක run කර ඇතිදැයි හෝ Settings හි Backend URL නිවැරදිදැයි පරීක්ෂා කරන්න.`
      );
    }
    throw err;
  }
}

export function buildVttContent(segments: any[]): string {
  let vtt = "WEBVTT\n\n";
  segments.forEach((s, idx) => {
    const formatTime = (seconds: number) => {
      const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
      const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
      const sec = (seconds % 60).toFixed(3).padStart(6, "0");
      return `${h}:${m}:${sec}`;
    };
    vtt += `${idx + 1}\n${formatTime(Number(s.start))} --> ${formatTime(Number(s.end))}\n${s.text}\n\n`;
  });
  return vtt;
}

export function buildSrtContent(segments: any[]): string {
  let srt = "";
  segments.forEach((s, idx) => {
    const formatTime = (seconds: number) => {
      const h = String(Math.floor(seconds / 3600)).padStart(2, "0");
      const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
      const secInt = String(Math.floor(seconds % 60)).padStart(2, "0");
      const ms = String(Math.floor((seconds % 1) * 1000)).padStart(3, "0");
      return `${h}:${m}:${secInt},${ms}`;
    };
    srt += `${idx + 1}\n${formatTime(Number(s.start))} --> ${formatTime(Number(s.end))}\n${s.text}\n\n`;
  });
  return srt;
}

export function downloadFile(content: string, filename: string, mimeType: string): boolean {
  try {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      try {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (e) {}
    }, 200);
    return true;
  } catch (err) {
    console.warn("Direct blob download restricted in iframe:", err);
    try {
      const encoded = encodeURIComponent(content);
      const dataUri = `data:${mimeType};charset=utf-8,${encoded}`;
      window.open(dataUri, "_blank");
      return true;
    } catch (e2) {
      return false;
    }
  }
}
