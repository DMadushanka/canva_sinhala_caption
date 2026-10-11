import os
import sys
import json
import time
import shutil
import threading
import webbrowser
import logging
import subprocess
import re
import tkinter as tk
from tkinter import ttk, messagebox

# Set up AppData config directory
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
    return os.environ.get("GEMINI_API_KEY", "").strip()

def save_key(key: str):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"gemini_api_key": key.strip()}, f)
    os.environ["GEMINI_API_KEY"] = key.strip()

def get_cloudflared_path() -> str:
    """Finds bundled or cached cloudflared executable."""
    candidates = []
    # 1. PyInstaller bundled path (_MEIPASS)
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        candidates.extend([
            os.path.join(base_dir, "cloudflared-windows-amd64.exe"),
            os.path.join(base_dir, "pycloudflared", "cloudflared-windows-amd64.exe"),
            os.path.join(os.path.dirname(sys.executable), "cloudflared-windows-amd64.exe"),
        ])
    # 2. Local backend folder candidates
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(curr_dir, "cloudflared-windows-amd64.exe"),
        os.path.join(curr_dir, "venv", "Lib", "site-packages", "pycloudflared", "cloudflared-windows-amd64.exe"),
        os.path.join(APPDATA_DIR, "cloudflared-windows-amd64.exe"),
    ])
    for c in candidates:
        if os.path.exists(c):
            return c

    # 3. pycloudflared package get_info
    try:
        from pycloudflared.util import get_info
        info = get_info()
        if os.path.exists(info.executable):
            return info.executable
    except Exception:
        pass

    return ""

class ServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8000):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        import uvicorn
        from app.main import app
        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True

class DesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sinhala Captions Engine for Canva")
        self.root.geometry("540x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#0e131f")

        self.server_thread = None
        self.tunnel_process = None
        self.tunnel_url = ""
        self.saved_key = load_saved_key()

        # Handle window closing cleanly
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build UI
        self.setup_ui()

        # Auto-start server and tunnel if key already present
        if self.saved_key:
            self.start_engine()

    def setup_ui(self):
        # Header banner
        header = tk.Frame(self.root, bg="#1a2035", height=75)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="සිං Sinhala Captions Engine",
            font=("Segoe UI", 15, "bold"),
            fg="#00c4cc",
            bg="#1a2035"
        )
        title.pack(anchor="w", padx=20, pady=(12, 2))

        subtitle = tk.Label(
            header,
            text="Cloud-Bridge AI Audio & Video Transcriber for Canva",
            font=("Segoe UI", 9),
            fg="#9ca3af",
            bg="#1a2035"
        )
        subtitle.pack(anchor="w", padx=20, pady=(0, 10))

        # Main Content container
        content = tk.Frame(self.root, bg="#0e131f")
        content.pack(fill="both", expand=True, padx=20, pady=14)

        # Status Card
        self.status_frame = tk.Frame(content, bg="#1a2035", relief="groove", bd=1)
        self.status_frame.pack(fill="x", pady=(0, 12), ipady=8, ipadx=10)

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

        # Canva Connection URL Card (PRIMARY FEATURE)
        url_card = tk.LabelFrame(
            content,
            text=" CANVA CONNECTION URL (HTTPS) ",
            font=("Segoe UI", 9, "bold"),
            fg="#00c4cc",
            bg="#131b2e",
            bd=1,
            relief="solid",
            padx=12,
            pady=10
        )
        url_card.pack(fill="x", pady=(0, 14))

        url_hint = tk.Label(
            url_card,
            text="Copy this HTTPS URL and paste it into Canva Plugin:",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="#131b2e"
        )
        url_hint.pack(anchor="w", pady=(0, 4))

        url_input_frame = tk.Frame(url_card, bg="#131b2e")
        url_input_frame.pack(fill="x", pady=(0, 8))

        self.url_entry = tk.Entry(
            url_input_frame,
            font=("Consolas", 10),
            bg="#0e131f",
            fg="#34d399",
            insertbackground="#00c4cc",
            relief="flat",
            bd=6
        )
        self.url_entry.insert(0, "Starting secure HTTPS tunnel...")
        self.url_entry.configure(state="readonly")
        self.url_entry.pack(fill="x")

        # Copy & Test Buttons row
        btn_row = tk.Frame(url_card, bg="#131b2e")
        btn_row.pack(fill="x")

        self.btn_copy_url = tk.Button(
            btn_row,
            text="📋 Copy URL for Canva",
            font=("Segoe UI", 10, "bold"),
            bg="#00c4cc",
            fg="#0e131f",
            activebackground="#00a0a8",
            activeforeground="#0e131f",
            relief="flat",
            cursor="hand2",
            state="disabled",
            command=self.copy_url_to_clipboard
        )
        self.btn_copy_url.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))

        self.btn_open_canva = tk.Button(
            btn_row,
            text="Open Canva ↗",
            font=("Segoe UI", 9),
            bg="#1f293d",
            fg="#d1d5db",
            activebackground="#374151",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=lambda: webbrowser.open("https://www.canva.com")
        )
        self.btn_open_canva.pack(side="right", ipady=4, ipadx=10)

        # Gemini API Key Section
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
            bd=6,
            show="*"
        )
        self.api_entry.pack(fill="x", pady=(0, 4))
        if self.saved_key:
            self.api_entry.insert(0, self.saved_key)

        # Key helpers row (Toggle show/hide & AI Studio link)
        key_helper_frame = tk.Frame(content, bg="#0e131f")
        key_helper_frame.pack(fill="x", pady=(0, 10))

        self.btn_toggle_key = tk.Label(
            key_helper_frame,
            text="👁 Show Key",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="#0e131f",
            cursor="hand2"
        )
        self.btn_toggle_key.pack(side="left")
        self.btn_toggle_key.bind("<Button-1>", self.toggle_key_visibility)

        link_btn = tk.Label(
            key_helper_frame,
            text="Get Free Gemini Key (aistudio.google.com) ↗",
            font=("Segoe UI", 8, "underline"),
            fg="#00c4cc",
            bg="#0e131f",
            cursor="hand2"
        )
        link_btn.pack(side="right")
        link_btn.bind("<Button-1>", lambda e: webbrowser.open("https://aistudio.google.com/app/apikey"))

        # Save & Restart Engine Button
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
        self.btn_save_start.pack(fill="x", ipady=6, pady=(0, 12))

        # Instructions Box
        guide_box = tk.Frame(content, bg="#131b2e", relief="flat", bd=1)
        guide_box.pack(fill="x", ipady=8, ipadx=10)

        guide_title = tk.Label(
            guide_box,
            text="How to Connect to Canva:",
            font=("Segoe UI", 9, "bold"),
            fg="#00c4cc",
            bg="#131b2e"
        )
        guide_title.pack(anchor="w")

        guide_text = tk.Label(
            guide_box,
            text="1. Click '📋 Copy URL for Canva' button above.\n2. In Canva, paste the URL into 'CLOUD BACKEND API URL'.\n3. Click 'Test Backend Connection' (it connects instantly).\n4. Keep this window running while using Canva!",
            font=("Segoe UI", 8),
            fg="#9ca3af",
            bg="#131b2e",
            justify="left"
        )
        guide_text.pack(anchor="w", pady=(3, 0))

    def toggle_key_visibility(self, event=None):
        if self.api_entry.cget("show") == "*":
            self.api_entry.configure(show="")
            self.btn_toggle_key.configure(text="🔒 Hide Key")
        else:
            self.api_entry.configure(show="*")
            self.btn_toggle_key.configure(text="👁 Show Key")

    def copy_url_to_clipboard(self):
        if not self.tunnel_url:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.tunnel_url)
        self.btn_copy_url.configure(text="✔ Copied to Clipboard!", bg="#10b981")
        self.root.after(2500, lambda: self.btn_copy_url.configure(text="📋 Copy URL for Canva", bg="#00c4cc"))

    def on_save_and_start(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showerror("Error", "Please enter a valid Gemini API Key from Google AI Studio.")
            return

        save_key(key)
        self.saved_key = key
        self.start_engine()

    def start_engine(self):
        os.environ["GEMINI_API_KEY"] = self.saved_key
        try:
            from app.config import settings
            settings.GEMINI_API_KEY = self.saved_key
        except Exception:
            pass

        # Update status UI
        self.status_indicator.configure(fg="#38bdf8")
        self.status_label.configure(text="Starting Engine & Secure HTTPS Bridge...")
        self.btn_save_start.configure(text="Engine Active (Click to Update Key)", bg="#059669")

        # 1. Start local Uvicorn FastAPI server on 127.0.0.1:8000
        if not self.server_thread or not self.server_thread.is_alive():
            self.server_thread = ServerThread(host="127.0.0.1", port=8000)
            self.server_thread.start()

        # 2. Start Cloudflare HTTPS tunnel thread
        threading.Thread(target=self.start_tunnel_worker, daemon=True).start()

    def start_tunnel_worker(self):
        # Wait 1.5 seconds for Uvicorn to bind port 8000
        time.sleep(1.5)

        cf_exe = get_cloudflared_path()
        if not cf_exe or not os.path.exists(cf_exe):
            try:
                from pycloudflared.util import get_info, download
                info = get_info()
                download(info)
                cf_exe = info.executable
            except Exception as e:
                logger.error(f"Failed to obtain cloudflared: {e}")

        if not cf_exe or not os.path.exists(cf_exe):
            self.root.after(0, self.on_tunnel_fallback, "http://localhost:8000")
            return

        # Terminate any previously running tunnel
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
            except Exception:
                pass

        try:
            args = [cf_exe, "tunnel", "--url", "http://127.0.0.1:8000"]
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.tunnel_process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )

            url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
            found_url = ""

            for _ in range(60):
                line = self.tunnel_process.stderr.readline()
                if not line:
                    break
                match = url_pattern.search(line)
                if match:
                    found_url = match.group(0)
                    break

            if found_url:
                self.tunnel_url = found_url
                self.root.after(0, self.on_tunnel_success, found_url)
            else:
                self.root.after(0, self.on_tunnel_fallback, "http://localhost:8000")

        except Exception as e:
            logger.error(f"Error launching tunnel: {e}")
            self.root.after(0, self.on_tunnel_fallback, "http://localhost:8000")

    def on_tunnel_success(self, url: str):
        self.tunnel_url = url
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, url)
        self.url_entry.configure(state="readonly")

        self.btn_copy_url.configure(state="normal")
        self.status_indicator.configure(fg="#10b981")
        self.status_label.configure(text="Engine Online & Connected to Canva (HTTPS)")

    def on_tunnel_fallback(self, fallback_url: str):
        self.tunnel_url = fallback_url
        self.url_entry.configure(state="normal")
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, fallback_url)
        self.url_entry.configure(state="readonly")

        self.btn_copy_url.configure(state="normal")
        self.status_indicator.configure(fg="#f59e0b")
        self.status_label.configure(text="Engine Online (Localhost Mode)")

    def on_close(self):
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
            except Exception:
                pass
        if self.server_thread:
            try:
                self.server_thread.stop()
            except Exception:
                pass
        self.root.destroy()
        sys.exit(0)

def main():
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
