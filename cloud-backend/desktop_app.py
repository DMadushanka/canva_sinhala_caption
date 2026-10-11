import os
import sys
import json
import threading
import webbrowser
import logging
import tkinter as tk
from tkinter import ttk, messagebox

# Set up appdata config directory
APPDATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "SinhalaCaptions")
CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")
os.makedirs(APPDATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SinhalaCaptionsEngine")

def load_saved_key() -> str:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("gemini_api_key", "").strip()
        except Exception:
            pass
    # Fallback to current .env or environment variable
    return os.environ.get("GEMINI_API_KEY", "").strip()

def save_key(key: str):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"gemini_api_key": key.strip()}, f)
    os.environ["GEMINI_API_KEY"] = key.strip()

class ServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8000):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        import uvicorn
        from app.main import app
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="info")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True

class DesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sinhala Captions Engine for Canva")
        self.root.geometry("480x420")
        self.root.resizable(False, False)
        self.root.configure(bg="#0e131f")

        self.server_thread = None
        self.saved_key = load_saved_key()

        # Build UI
        self.setup_ui()

        # Auto-start if key already present
        if self.saved_key:
            self.start_server()

    def setup_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#1a2035", height=70)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="සිං Sinhala Captions Engine",
            font=("Segoe UI", 14, "bold"),
            fg="#00c4cc",
            bg="#1a2035"
        )
        title.pack(anchor="w", padx=20, pady=(12, 2))

        subtitle = tk.Label(
            header,
            text="Local AI Speech-to-Text Server for Canva Plugin",
            font=("Segoe UI", 9),
            fg="#9ca3af",
            bg="#1a2035"
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 10))

        # Main Content container
        content = tk.Frame(self.root, bg="#0e131f")
        content.pack(fill="both", expand=True, padx=20, pady=16)

        # Status badge
        self.status_frame = tk.Frame(content, bg="#1a2035", relief="groove", bd=1)
        self.status_frame.pack(fill="x", pady=(0, 14), ipady=8, ipadx=10)

        self.status_indicator = tk.Label(
            self.status_frame,
            text="●",
            font=("Segoe UI", 16),
            fg="#f59e0b",
            bg="#1a2035"
        )
        self.status_indicator.pack(side="left", padx=(10, 6))

        self.status_label = tk.Label(
            self.status_frame,
            text="Engine Stopped - Gemini API Key Required",
            font=("Segoe UI", 10, "bold"),
            fg="#f3f4f6",
            bg="#1a2035"
        )
        self.status_label.pack(side="left")

        # API Key Section
        api_label = tk.Label(
            content,
            text="Gemini API Key (Google AI Studio):",
            font=("Segoe UI", 9, "bold"),
            fg="#d1d5db",
            bg="#0e131f"
        )
        api_label.pack(anchor="w", pady=(0, 4))

        self.api_entry = tk.Entry(
            content,
            font=("Consolas", 10),
            bg="#1f293d",
            fg="#ffffff",
            insertbackground="#00c4cc",
            relief="flat",
            bd=6
        )
        self.api_entry.pack(fill="x", pady=(0, 6))
        if self.saved_key:
            self.api_entry.insert(0, self.saved_key)

        # Helper link
        link_frame = tk.Frame(content, bg="#0e131f")
        link_frame.pack(fill="x", pady=(0, 14))

        link_btn = tk.Label(
            link_frame,
            text="Get Free Gemini API Key (aistudio.google.com) ↗",
            font=("Segoe UI", 8, "underline"),
            fg="#00c4cc",
            bg="#0e131f",
            cursor="hand2"
        )
        link_btn.pack(side="left")
        link_btn.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        # Action Buttons
        self.btn_save_start = tk.Button(
            content,
            text="Save Key & Start Engine",
            font=("Segoe UI", 10, "bold"),
            bg="#7d2ae8",
            fg="#ffffff",
            activebackground="#6b21a8",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self.on_save_and_start
        )
        self.btn_save_start.pack(fill="x", ipady=6, pady=(0, 10))

        # Canva Connection Note
        note_box = tk.Frame(content, bg="#131b2e", relief="flat", bd=1)
        note_box.pack(fill="x", pady=(6, 0), ipady=8, ipadx=10)

        note_title = tk.Label(
            note_box,
            text="How to use in Canva:",
            font=("Segoe UI", 9, "bold"),
            fg="#00c4cc",
            bg="#131b2e"
        )
        note_title.pack(anchor="w")

        note_text = tk.Label(
            note_box,
            text="1. Keep this app running while using Canva.\n2. In Canva, open Sinhala Captions App.\n3. Upload audio/video & click Generate Captions!",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="#131b2e",
            justify="left"
        )
        note_text.pack(anchor="w", pady=(2, 0))

    def on_save_and_start(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter a valid Gemini API Key.")
            return

        save_key(key)
        self.saved_key = key
        self.start_server()

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            return

        os.environ["GEMINI_API_KEY"] = self.saved_key
        # Update config module in memory
        try:
            from app.config import settings
            settings.GEMINI_API_KEY = self.saved_key
        except Exception:
            pass

        self.server_thread = ServerThread(host="0.0.0.0", port=8000)
        self.server_thread.start()

        self.status_indicator.configure(fg="#10b981")
        self.status_label.configure(text="Engine Running Online (http://localhost:8000)")
        self.btn_save_start.configure(text="Engine is Active (Click to Update Key)", bg="#059669")

def main():
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
