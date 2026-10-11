import React, { useState, useRef } from "react";
import {
  Sparkles,
  Upload,
  FileVideo,
  Download,
  PlusCircle,
  Settings2,
  Subtitles,
  Trash2,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { SubtitleSegment, CaptionStyle } from "./types";
import { transcribeMedia, downloadFile, getBackendUrl, setBackendUrl, checkBackendHealth } from "./services/api";
import { addCaptionToCanva } from "./services/canvaSdk";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"upload" | "editor" | "styling">("upload");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [engine, setEngine] = useState<"google" | "gemini">("google");
  const [wordsPerChunk, setWordsPerChunk] = useState<number>(5);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [customBackendUrl, setCustomBackendUrl] = useState<string>(getBackendUrl());
  const [backendHealth, setBackendHealth] = useState<string | null>(null);

  // Subtitles state
  const [segments, setSegments] = useState<SubtitleSegment[]>([]);
  const [srtData, setSrtData] = useState<string>("");
  const [vttData, setVttData] = useState<string>("");

  // Styling state
  const [style, setStyle] = useState<CaptionStyle>({
    preset: "bold_glow",
    fontFamily: "Noto Sans Sinhala",
    fontSize: 28,
    textColor: "#ffffff",
    strokeColor: "#000000",
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    position: "bottom",
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  // Demo Sinhala data loader for instant preview
  const handleLoadDemo = () => {
    const demoSegments: SubtitleSegment[] = [
      {
        id: 1,
        start: 0.0,
        end: 2.5,
        text: "ආයුබෝවන් සියලු දෙනාටම",
      },
      {
        id: 2,
        start: 2.6,
        end: 5.2,
        text: "අද අපි බලමු කැන්වා වීඩියෝ වලට උපසිරැසි දාන්නේ කොහොමද කියලා",
      },
      {
        id: 3,
        start: 5.3,
        end: 8.0,
        text: "ස්වයංක්‍රීය සිංහල උපසිරැසි තාක්ෂණය",
      },
    ];
    setSegments(demoSegments);
    setActiveTab("editor");
    setSuccessMsg("ආදර්ශ සිංහල උපසිරැසි සාර්ථකව පූරණය විය (Sample data loaded)");
  };

  // Start transcription via Cloud STT Backend
  const handleGenerateCaptions = async () => {
    if (!selectedFile) {
      setErrorMsg("කරුණාකර වීඩියෝ හෝ ශ්‍රව්‍ය ගොනුවක් තෝරන්න (Please select a video/audio file)");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const response = await transcribeMedia(selectedFile, engine, wordsPerChunk);
      setSegments(response.segments);
      setSrtData(response.srt);
      setVttData(response.vtt);
      setActiveTab("editor");
      setSuccessMsg(`සාර්ථකයි! සිංහල උපසිරැසි කොටස් ${response.segments.length} ක් නිර්මාණය විය.`);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate Sinhala captions from Cloud Backend");
    } finally {
      setIsLoading(false);
    }
  };

  // Update text of a specific subtitle segment
  const handleSegmentTextChange = (id: number, newText: string) => {
    setSegments((prev) =>
      prev.map((seg) => (seg.id === id ? { ...seg, text: newText } : seg))
    );
  };

  // Add caption segment to Canva Canvas
  const handleAddToCanva = async (seg: SubtitleSegment) => {
    const ok = await addCaptionToCanva(seg, style);
    if (ok) {
      setSuccessMsg(`"${seg.text.slice(0, 20)}..." Canva පිටුවට එක් කරන ලදී!`);
      setTimeout(() => setSuccessMsg(null), 3000);
    }
  };

  // Export SRT
  const handleExportSRT = () => {
    if (srtData) {
      downloadFile(srtData, "sinhala_captions.srt", "application/x-subrip");
    } else if (segments.length > 0) {
      // Build basic srt on the fly
      let srtContent = "";
      segments.forEach((s, idx) => {
        srtContent += `${idx + 1}\n00:00:0${Math.floor(s.start)},000 --> 00:00:0${Math.floor(s.end)},000\n${s.text}\n\n`;
      });
      downloadFile(srtContent, "sinhala_captions.srt", "application/x-subrip");
    }
  };

  // Export VTT
  const handleExportVTT = () => {
    if (vttData) {
      downloadFile(vttData, "sinhala_captions.vtt", "text/vtt");
    } else if (segments.length > 0) {
      let vttContent = "WEBVTT\n\n";
      segments.forEach((s, idx) => {
        vttContent += `${idx + 1}\n00:00:0${Math.floor(s.start)}.000 --> 00:00:0${Math.floor(s.end)}.000\n${s.text}\n\n`;
      });
      downloadFile(vttContent, "sinhala_captions.vtt", "text/vtt");
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-icon">සිං</div>
          <div>
            <h1 className="brand-title">Sinhala Captions</h1>
            <div className="brand-subtitle">සිංහල වීඩියෝ උපසිරැසි AI</div>
          </div>
        </div>
        <span className="badge-cloud">Cloud STT</span>
      </header>

      {/* Navigation Tabs */}
      <nav className="tabs-nav">
        <button
          className={`tab-btn ${activeTab === "upload" ? "active" : ""}`}
          onClick={() => setActiveTab("upload")}
        >
          <Upload size={14} /> Upload
        </button>
        <button
          className={`tab-btn ${activeTab === "editor" ? "active" : ""}`}
          onClick={() => setActiveTab("editor")}
        >
          <Subtitles size={14} /> Subtitles ({segments.length})
        </button>
        <button
          className={`tab-btn ${activeTab === "styling" ? "active" : ""}`}
          onClick={() => setActiveTab("styling")}
        >
          <Settings2 size={14} /> Style
        </button>
      </nav>

      {/* Notifications */}
      {errorMsg && (
        <div style={{ background: "rgba(255, 73, 128, 0.15)", border: "1px solid rgba(255, 73, 128, 0.4)", borderRadius: 8, padding: 10, marginBottom: 12, display: "flex", gap: 8, alignItems: "center", color: "#ff4980", fontSize: 12 }}>
          <AlertCircle size={16} />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div style={{ background: "rgba(0, 196, 204, 0.15)", border: "1px solid rgba(0, 196, 204, 0.4)", borderRadius: 8, padding: 10, marginBottom: 12, display: "flex", gap: 8, alignItems: "center", color: "#00c4cc", fontSize: 12 }}>
          <CheckCircle2 size={16} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* TAB 1: UPLOAD & GENERATE */}
      {activeTab === "upload" && (
        <div>
          {/* File Upload Box */}
          <div className="card-section">
            <div className="section-label">Video / Audio Source</div>
            <input
              type="file"
              ref={fileInputRef}
              accept="video/*,audio/*"
              style={{ display: "none" }}
              onChange={handleFileChange}
            />
            <div
              className="dropzone"
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="dropzone-icon">
                <FileVideo size={22} />
              </div>
              <div className="dropzone-title">Upload Video or Audio</div>
              <div className="dropzone-desc">MP4, MOV, WEBM, MP3, WAV (Up to 100MB)</div>
            </div>

            {selectedFile && (
              <div className="file-pill">
                <div className="file-info">
                  <FileVideo size={16} color="#00c4cc" />
                  <span className="file-name">{selectedFile.name}</span>
                </div>
                <button
                  className="btn-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            )}
          </div>

          {/* AI Settings */}
          <div className="card-section">
            <div className="section-label">AI Engine & Language</div>
            <div className="form-group">
              <label className="form-label">Speech-to-Text Model</label>
              <select
                className="select-control"
                value={engine}
                onChange={(e) => setEngine(e.target.value as any)}
              >
                <option value="gemini">Gemini 3 Flash Audio - Highest Accuracy & Punctuation</option>
                <option value="google">Google Cloud STT (si-LK) - Traditional Phonetics</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Words Per Caption Chunk</label>
              <select
                className="select-control"
                value={wordsPerChunk}
                onChange={(e) => setWordsPerChunk(Number(e.target.value))}
              >
                <option value={3}>3 Words (Fast / TikTok Style)</option>
                <option value={5}>5 Words (Standard Video Reading)</option>
                <option value={7}>7 Words (Full Sentence Subtitle)</option>
              </select>
            </div>
          </div>

          {/* Action Button */}
          <button
            className="btn-primary"
            onClick={handleGenerateCaptions}
            disabled={isLoading || !selectedFile}
          >
            {isLoading ? (
              <>
                <div className="spinner" />
                <span>Generating Sinhala Captions...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Generate Captions (උපසිරැසි හදන්න)</span>
              </>
            )}
          </button>

          <div style={{ textAlign: "center", marginTop: 12 }}>
            <button
              onClick={handleLoadDemo}
              style={{ background: "transparent", border: "none", color: "#9ca3af", fontSize: 11, cursor: "pointer", textDecoration: "underline" }}
            >
              Load Demo Sinhala Captions (නියැදි දත්ත බලන්න)
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: SUBTITLES LIST & EDITOR */}
      {activeTab === "editor" && (
        <div>
          {/* Live Mockup Preview */}
          <div className="mockup-preview-box">
            <div className="mockup-canvas-bg" />
            <div
              className="mockup-caption-text"
              style={{
                fontFamily: style.fontFamily,
                fontSize: style.fontSize * 0.55,
                color: style.textColor,
                backgroundColor: style.preset === "karaoke_box" ? style.backgroundColor : "transparent",
                textShadow: style.preset === "bold_glow" ? "0 0 10px rgba(0, 196, 204, 0.8), 2px 2px 4px #000" : "1px 1px 3px #000",
                border: style.preset === "bold_glow" ? "1px solid rgba(0, 196, 204, 0.4)" : "none",
              }}
            >
              {segments.length > 0
                ? segments[0].text
                : "ස්වයංක්‍රීය සිංහල උපසිරැසි පෙරදසුන (Preview)"}
            </div>
          </div>

          <div className="card-section">
            <div className="section-label">
              <span>Sinhala Segments ({segments.length})</span>
              <button
                onClick={() => setSegments([])}
                style={{ background: "transparent", border: "none", color: "#9ca3af", fontSize: 11, cursor: "pointer" }}
              >
                Clear
              </button>
            </div>

            {segments.length === 0 ? (
              <div style={{ textAlign: "center", padding: "20px 0", color: "#6b7280", fontSize: 12 }}>
                තවමත් උපසිරැසි නිර්මාණය කර නැත. Upload පිටුවට ගොස් වීඩියෝවක් තෝරන්න.
              </div>
            ) : (
              <div className="segments-list">
                {segments.map((seg) => (
                  <div key={seg.id} className="segment-item">
                    <div className="segment-meta">
                      <span className="segment-time">
                        {seg.start}s - {seg.end}s
                      </span>
                      <button
                        className="btn-secondary"
                        style={{ padding: "3px 8px", fontSize: 10 }}
                        onClick={() => handleAddToCanva(seg)}
                        title="Add this caption line directly to Canva canvas"
                      >
                        <PlusCircle size={11} /> To Canvas
                      </button>
                    </div>
                    <textarea
                      className="segment-input"
                      rows={2}
                      value={seg.text}
                      onChange={(e) => handleSegmentTextChange(seg.id, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Export Actions */}
          {segments.length > 0 && (
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn-secondary" onClick={handleExportSRT}>
                <Download size={13} /> Export .SRT
              </button>
              <button className="btn-secondary" onClick={handleExportVTT}>
                <Download size={13} /> Export .VTT
              </button>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: STYLING & PRESETS */}
      {activeTab === "styling" && (
        <div>
          <div className="card-section">
            <div className="section-label">Caption Style Presets</div>
            <div className="preset-grid">
              <div
                className={`preset-card ${style.preset === "bold_glow" ? "active" : ""}`}
                onClick={() => setStyle({ ...style, preset: "bold_glow" })}
              >
                <div className="preset-title">TikTok Glow</div>
                <div className="preset-preview-text" style={{ color: "#00c4cc", fontWeight: 700 }}>
                  සිංහල අකුරු
                </div>
              </div>

              <div
                className={`preset-card ${style.preset === "karaoke_box" ? "active" : ""}`}
                onClick={() => setStyle({ ...style, preset: "karaoke_box" })}
              >
                <div className="preset-title">Karaoke Box</div>
                <div className="preset-preview-text" style={{ background: "#222", padding: "2px 4px", borderRadius: 4 }}>
                  සිංහල අකුරු
                </div>
              </div>

              <div
                className={`preset-card ${style.preset === "classic_subtitle" ? "active" : ""}`}
                onClick={() => setStyle({ ...style, preset: "classic_subtitle" })}
              >
                <div className="preset-title">Classic Film</div>
                <div className="preset-preview-text" style={{ color: "#ffd700" }}>
                  සිංහල අකුරු
                </div>
              </div>

              <div
                className={`preset-card ${style.preset === "cinematic" ? "active" : ""}`}
                onClick={() => setStyle({ ...style, preset: "cinematic" })}
              >
                <div className="preset-title">Minimal Clean</div>
                <div className="preset-preview-text" style={{ color: "#ffffff" }}>
                  සිංහල අකුරු
                </div>
              </div>
            </div>
          </div>

          <div className="card-section">
            <div className="section-label">Typography & Appearance</div>

            <div className="form-group">
              <label className="form-label">Sinhala Font Family</label>
              <select
                className="select-control"
                value={style.fontFamily}
                onChange={(e) => setStyle({ ...style, fontFamily: e.target.value })}
              >
                <option value="Noto Sans Sinhala">Noto Sans Sinhala (Clean Unicode)</option>
                <option value="Abhaya Libre">Abhaya Libre (Classic Serif)</option>
                <option value="Inter">Inter (Modern Sans)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Font Size ({style.fontSize}px)</label>
              <input
                type="range"
                min={16}
                max={48}
                value={style.fontSize}
                onChange={(e) => setStyle({ ...style, fontSize: Number(e.target.value) })}
                style={{ width: "100%", accentColor: "#7d2ae8" }}
              />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div className="form-group">
                <label className="form-label">Text Color</label>
                <input
                  type="color"
                  className="input-control"
                  style={{ height: 38, padding: 2, cursor: "pointer" }}
                  value={style.textColor}
                  onChange={(e) => setStyle({ ...style, textColor: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Box Background</label>
                <input
                  type="color"
                  className="input-control"
                  style={{ height: 38, padding: 2, cursor: "pointer" }}
                  value="#000000"
                  onChange={(e) => setStyle({ ...style, backgroundColor: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Backend Connection Card */}
          <div className="card-section">
            <div className="section-label">Cloud Backend API URL</div>
            <div className="form-group">
              <input
                type="text"
                className="input-control"
                value={customBackendUrl}
                placeholder="e.g. http://localhost:8000 or https://your-cloud-run-url"
                onChange={(e) => {
                  setCustomBackendUrl(e.target.value);
                  setBackendUrl(e.target.value);
                }}
              />
            </div>
            <button
              className="btn-secondary"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={async () => {
                setBackendHealth("Testing connection...");
                const res = await checkBackendHealth();
                setBackendHealth(res.ok ? `✅ ${res.message}` : `❌ ${res.message}`);
              }}
            >
              Test Backend Connection
            </button>
            {backendHealth && (
              <div style={{ marginTop: 8, fontSize: 11, textAlign: "center", color: backendHealth.startsWith("✅") ? "#00c4cc" : "#ff4980" }}>
                {backendHealth}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
