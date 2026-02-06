"""
Audio Recorder for Voice Workflows
Handles recording, transcription, and state management
"""

import threading
import time
from typing import Optional, Callable
import sys
import types

# Import recording indicator for visual feedback
try:
    from recording_indicator import show_recording_indicator, hide_recording_indicator
    INDICATOR_AVAILABLE = True
except ImportError:
    INDICATOR_AVAILABLE = False
    print("⚠️  Recording indicator not available")

# Stub out modules for Python 3.13+ compatibility
for _mod_name in ("aifc", "audioop"):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = types.ModuleType(_mod_name)

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


class AudioRecorder:
    """Handles audio recording and transcription for voice workflows"""

    def __init__(self):
        self.is_recording = False
        self.audio_buffer = []
        self.stream = None
        self.recognizer = sr.Recognizer() if sr else None
        self.sample_rate = 16000
        self.transcription = None
        self.on_transcription_complete: Optional[Callable[[str], None]] = None

    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            print("   ⚠️  Already recording")
            return False

        if not sd or not np:
            print("   ❌ sounddevice/numpy not installed")
            return False

        self.is_recording = True
        self.audio_buffer = []
        self.transcription = None

        print("   🔴 Recording started...")

        # Show visual indicator
        if INDICATOR_AVAILABLE:
            try:
                show_recording_indicator()
            except Exception as e:
                print(f"   ⚠️  Could not show indicator: {e}")

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"   ❌ Failed to start recording: {e}")
            self.is_recording = False
            # Hide indicator if start failed
            if INDICATOR_AVAILABLE:
                try:
                    hide_recording_indicator()
                except:
                    pass
            return False

    def stop_recording(self):
        """Stop recording and start transcription"""
        if not self.is_recording:
            print("   ⚠️  Not currently recording")
            return False

        self.is_recording = False

        # Hide visual indicator
        if INDICATOR_AVAILABLE:
            try:
                hide_recording_indicator()
            except Exception as e:
                print(f"   ⚠️  Could not hide indicator: {e}")

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("   ⏹️  Recording stopped")
        print("   🔄 Transcribing...")

        # Start transcription in background thread
        threading.Thread(target=self._transcribe, daemon=True).start()
        return True

    def _audio_callback(self, indata, frames, timeinfo, status):
        """Called by sounddevice on audio thread"""
        if self.is_recording:
            self.audio_buffer.append(indata.copy())

    def _transcribe(self):
        """Transcribe recorded audio using Google Speech Recognition"""
        if not self.audio_buffer:
            print("   ⚠️  No audio captured")
            return

        try:
            # Combine audio chunks
            combined = np.vstack(self.audio_buffer)
            audio_data = sr.AudioData(combined.tobytes(), self.sample_rate, 2)

            # Transcribe using Google
            text = self.recognizer.recognize_google(audio_data, language="en-US")

            self.transcription = text
            print(f"   ✅ Transcribed: {text[:100]}...")

            # Call callback if registered
            if self.on_transcription_complete:
                self.on_transcription_complete(text)

        except sr.UnknownValueError:
            print("   ⚠️  Could not understand audio")
            self.transcription = None
        except sr.RequestError as e:
            print(f"   ⚠️  API error: {e}")
            self.transcription = None
        except Exception as e:
            print(f"   ❌ Transcription error: {e}")
            import traceback
            traceback.print_exc()
            self.transcription = None

    def get_transcription(self) -> Optional[str]:
        """Get the transcription result"""
        return self.transcription

    def is_busy(self) -> bool:
        """Check if recording or transcribing"""
        return self.is_recording
