# Canva Sinhala Caption Plugin (Frontend App)

This frontend application is built for the **Canva Apps SDK** to provide creators with automated, synchronized Sinhala subtitles right inside the Canva video editor.

---

## 🌟 Key Capabilities
- **Canva Editor Integration**: Embeds into the Canva side panel with native theme styling.
- **Sinhala Typography**: Supports clean Sinhala Unicode rendering (*Noto Sans Sinhala*, *Abhaya Libre*).
- **Custom Caption Presets**: TikTok/Reels Glow, Karaoke Box, Classic Film, and Minimal Clean.
- **Interactive Line Editor**: Edit and adjust transcribed Sinhala text directly before applying.
- **Export Standards**: 1-click export of UTF-8 encoded `.srt` and `.vtt` caption tracks.

---

## 🚀 Running Locally

```bash
cd canva-app
npm install
npm run dev
```
The app will run at `http://localhost:3000`.

---

## 🛠️ Canva Developer Portal Configuration

To run and preview this app inside the actual Canva editor:

1. Go to the [Canva Developers Portal](https://www.canva.com/developers/).
2. Click **Create an app**.
3. Under **App Configuration**:
   - Set **Development URL** to `http://localhost:3000` (or your deployed HTTPS URL).
4. Under **Required Permissions / Scopes**:
   - `canva:design:content:write` (to insert caption text elements onto the canvas)
   - `canva:asset:read` (to detect audio/video in the design)
5. Click **Preview in Canva** to open a video editor session with your Sinhala Caption app loaded in the sidebar!
