"""
HackApp Speech-to-Text

Standalone app: records from mic, transcribes via Google, auto-copies to clipboard.
Then press Ctrl+Alt+M in DXCare to trigger the agent workflow.

Run:  python speech_app/main.py
"""

import sys
import types

# aifc and audioop were removed in Python 3.13+; speech_recognition still
# imports them at module level.  We only use the Google HTTP backend so the
# actual functionality is never called — stub them out before the import.
for _mod_name in ("aifc", "audioop"):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = types.ModuleType(_mod_name)

import tkinter as tk
from tkinter import ttk
import threading
import pyperclip

try:
    import numpy as np
    import sounddevice as sd
except ImportError:
    np = None
    sd = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


# ============================================================================
# Configuration
# ============================================================================

SAMPLE_RATE = 16000  # 16 kHz — standard for speech recognition

LANGUAGES = {
    "French": "fr-FR",
    "English (US)": "en-US",
    "English (UK)": "en-GB",
}


# ============================================================================
# Helper – enumerate input devices
# ============================================================================

def _get_input_devices():
    """Return list of (device_index, label) for every input-capable device."""
    if sd is None:
        return []
    devices = sd.query_devices()
    result = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            result.append((i, f"{dev['name']}"))
    return result


# ============================================================================
# App
# ============================================================================

class SpeechToTextApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HackApp - Speech to Text")
        self.root.geometry("460x440")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.is_recording = False
        self.audio_buffer = []          # list of numpy arrays
        self.stream = None              # sd.InputStream instance while recording
        self.recognizer = sr.Recognizer() if sr else None

        # Device list: [(index, label), ...]
        self.input_devices = _get_input_devices()
        # Map label → index for quick lookup
        self._device_index = {label: idx for idx, label in self.input_devices}

        self._build_ui()
        self._check_deps()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#181825", pady=14)
        header.pack(fill="x")
        tk.Label(header, text="🎤  Speech to Text",
                 font=("Helvetica", 16, "bold"),
                 fg="white", bg="#181825").pack()

        # Body
        body = tk.Frame(self.root, bg="#1e1e2e")
        body.pack(fill="both", expand=True, padx=22, pady=10)

        # ── Microphone selector ────────────────────────────────────────
        mic_row = tk.Frame(body, bg="#1e1e2e")
        mic_row.pack(fill="x", pady=(0, 4))
        tk.Label(mic_row, text="Mic:",
                 font=("Helvetica", 10), fg="#cdd6f4", bg="#1e1e2e",
                 width=8, anchor="w").pack(side="left")

        mic_labels = [label for _, label in self.input_devices]
        self.mic_var = tk.StringVar(value=mic_labels[0] if mic_labels else "")
        self.mic_combo = ttk.Combobox(mic_row, textvariable=self.mic_var,
                                      values=mic_labels,
                                      state="readonly", width=38)
        self.mic_combo.pack(side="left")

        # ── Language selector ──────────────────────────────────────────
        lang_row = tk.Frame(body, bg="#1e1e2e")
        lang_row.pack(fill="x", pady=(4, 4))
        tk.Label(lang_row, text="Language:",
                 font=("Helvetica", 10), fg="#cdd6f4", bg="#1e1e2e",
                 width=8, anchor="w").pack(side="left")
        self.lang_var = tk.StringVar(value="French")
        ttk.Combobox(lang_row, textvariable=self.lang_var,
                     values=list(LANGUAGES.keys()),
                     state="readonly", width=20).pack(side="left")

        # ── Level indicator ────────────────────────────────────────────
        self.level_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.level_var,
                 font=("Consolas", 10), fg="#a6e3a1", bg="#1e1e2e",
                 anchor="w").pack(fill="x", pady=(6, 2))

        # ── Record button ──────────────────────────────────────────────
        self.record_btn = tk.Button(
            body, text="⏺  Start Recording",
            font=("Helvetica", 13, "bold"),
            bg="#f38ba8", fg="#1e1e2e", activebackground="#f2739c",
            relief="flat", bd=0, padx=24, pady=10,
            command=self.toggle_recording, cursor="hand2"
        )
        self.record_btn.pack(pady=(8, 4))

        # ── Status ─────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready — press record to start")
        tk.Label(body, textvariable=self.status_var,
                 font=("Helvetica", 10), fg="#a6adc8", bg="#1e1e2e").pack(pady=(0, 6))

        # ── Transcription output ───────────────────────────────────────
        tk.Label(body, text="Transcribed text",
                 font=("Helvetica", 9, "bold"), fg="#7f849c",
                 bg="#1e1e2e", anchor="w").pack(fill="x", pady=(4, 2))

        text_frame = tk.Frame(body, bg="#313244")
        text_frame.pack(fill="both", expand=True)
        self.text_area = tk.Text(
            text_frame, height=4, font=("Consolas", 11),
            bg="#313244", fg="#cdd6f4", insertbackground="white",
            relief="flat", bd=8, spacing1=4
        )
        self.text_area.pack(fill="both", expand=True)
        self.text_area.config(state="disabled")

        # Footer
        tk.Label(self.root,
                 text="Auto-copies to clipboard  •  Press Ctrl+Alt+M in DXCare to paste",
                 font=("Helvetica", 8), fg="#585b70", bg="#1e1e2e").pack(pady=(4, 8))

    def _check_deps(self):
        missing = []
        if not sd or not np:
            missing.append("sounddevice numpy")
        if not sr:
            missing.append("SpeechRecognition")
        if missing:
            self.status_var.set(f"⚠  Install missing: pip install {' '.join(missing)}")
            self.record_btn.config(state="disabled")

    # ------------------------------------------------------------------
    # Recording  (InputStream callback-based — no gaps between chunks)
    # ------------------------------------------------------------------

    def toggle_recording(self):
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _selected_device_index(self):
        """Return the sounddevice index for the currently selected mic."""
        label = self.mic_var.get()
        return self._device_index.get(label, None)

    def _start_recording(self):
        self.is_recording = True
        self.audio_buffer = []
        self.record_btn.config(text="⏹  Stop", bg="#a6e3a1", fg="#1e1e2e")
        self.status_var.set("🔴  Recording…")
        self._set_text("")

        device_idx = self._selected_device_index()
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            device=device_idx,
            callback=self._audio_callback,
            blocksize=int(SAMPLE_RATE * 0.1),  # 100 ms blocks
        )
        self.stream.start()
        # Schedule the first level-indicator tick
        self._update_level()

    def _audio_callback(self, indata, frames, timeinfo, status):
        """Called by sounddevice on the audio thread — just buffer the data."""
        if self.is_recording:
            self.audio_buffer.append(indata.copy())

    def _update_level(self):
        """Refresh the level bar every 100 ms while recording."""
        if not self.is_recording:
            self.level_var.set("")
            return

        if self.audio_buffer:
            latest = self.audio_buffer[-1]
            rms = int(np.sqrt(np.mean(latest.astype(np.float64) ** 2)))
        else:
            rms = 0

        # Map RMS (0-32767 for int16) to a bar of up to 30 chars
        bar_len = min(int(rms / 1000), 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        self.level_var.set(f"Level: [{bar}] {rms}")

        # Keep ticking
        self.root.after(100, self._update_level)

    def _stop_recording(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.level_var.set("")
        self.record_btn.config(state="disabled", text="🔄  Transcribing…",
                               bg="#f9e2af", fg="#1e1e2e")
        self.status_var.set("Processing audio…")
        threading.Thread(target=self._transcribe, daemon=True).start()

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def _transcribe(self):
        if not self.audio_buffer:
            self._set_status("⚠  No audio captured — try again")
            return

        try:
            combined = np.vstack(self.audio_buffer)
            audio_data = sr.AudioData(combined.tobytes(), SAMPLE_RATE, 2)  # int16 = 2 bytes

            lang_code = LANGUAGES.get(self.lang_var.get(), "fr-FR")
            text = self.recognizer.recognize_google(audio_data, language=lang_code)

            # Success
            self._set_text(text)
            pyperclip.copy(text)
            self._set_status("✅  Copied to clipboard — press Ctrl+Alt+M in DXCare")

        except sr.UnknownValueError:
            self._set_status("⚠  Could not understand audio — try again")
        except sr.RequestError as e:
            self._set_status(f"⚠  API error (internet required): {e}")
        except Exception as e:
            self._set_status(f"⚠  Error: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg):
        self.status_var.set(msg)
        self.record_btn.config(state="normal", text="⏺  Start Recording",
                               bg="#f38ba8", fg="#1e1e2e")

    def _set_text(self, text):
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", "end")
        if text:
            self.text_area.insert("end", text)
        self.text_area.config(state="disabled")

    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SpeechToTextApp()
    app.run()
