"""
Audio Recorder for Voice Workflows
Handles recording, transcription, and state management
"""

import threading
import time
from typing import Optional, Callable
import sys
import types

# Stub out modules for Python 3.13+ compatibility FIRST
for _mod_name in ("aifc", "audioop"):
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = types.ModuleType(_mod_name)

try:
    import numpy as np
    import sounddevice as sd
except (ImportError, OSError) as e:
    # OSError raised when PortAudio library not found
    # ImportError raised when packages not installed
    np = None
    sd = None
    if "PortAudio" not in str(e):
        print(f"⚠️  Audio libraries not available: {e}")

try:
    import speech_recognition as sr
except ImportError:
    sr = None

# Import recording indicator for visual feedback (after other imports)
try:
    from .recording_indicator import show_recording_indicator, hide_recording_indicator
    INDICATOR_AVAILABLE = True
except ImportError:
    try:
        # Fallback for direct execution
        from recording_indicator import show_recording_indicator, hide_recording_indicator
        INDICATOR_AVAILABLE = True
    except ImportError:
        INDICATOR_AVAILABLE = False
        # Silently fail - indicator is optional


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
        print("   🔍 [DEBUG] start_recording() called")

        if self.is_recording:
            print("   ⚠️  Already recording")
            return False

        if not sd or not np:
            print("   ❌ sounddevice/numpy not installed")
            print(f"   🔍 [DEBUG] sd={sd}, np={np}")
            return False

        self.is_recording = True
        self.audio_buffer = []
        self.transcription = None

        print("   🔴 Recording started...")
        print(f"   🔍 [DEBUG] Sample rate: {self.sample_rate}")
        print(f"   🔍 [DEBUG] Buffer initialized: {len(self.audio_buffer)} chunks")

        # Show visual indicator
        if INDICATOR_AVAILABLE:
            try:
                show_recording_indicator()
                print("   ✅ [DEBUG] Visual indicator shown")
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
            print("   ✅ [DEBUG] Audio stream started successfully")
            return True
        except Exception as e:
            print(f"   ❌ Failed to start recording: {e}")
            import traceback
            traceback.print_exc()
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
        print("   🔍 [DEBUG] stop_recording() called")

        if not self.is_recording:
            print("   ⚠️  Not currently recording")
            return False

        self.is_recording = False

        # Hide visual indicator
        if INDICATOR_AVAILABLE:
            try:
                hide_recording_indicator()
                print("   ✅ [DEBUG] Visual indicator hidden")
            except Exception as e:
                print(f"   ⚠️  Could not hide indicator: {e}")

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("   ✅ [DEBUG] Audio stream stopped and closed")

        print(f"   🔍 [DEBUG] Captured {len(self.audio_buffer)} audio chunks")
        print("   ⏹️  Recording stopped")
        print("   🔄 Transcribing...")

        # Start transcription in background thread
        print("   🔍 [DEBUG] Starting transcription thread...")
        threading.Thread(target=self._transcribe, daemon=True).start()
        return True

    def _audio_callback(self, indata, frames, timeinfo, status):
        """Called by sounddevice on audio thread"""
        if self.is_recording:
            self.audio_buffer.append(indata.copy())
            # Print every 10 chunks to avoid spam
            if len(self.audio_buffer) % 10 == 0:
                print(f"   🔍 [DEBUG] Audio chunks captured: {len(self.audio_buffer)}")

    def _transcribe(self):
        """Transcribe recorded audio using Google Speech Recognition"""
        print("   🔍 [DEBUG] _transcribe() thread started")

        if not self.audio_buffer:
            print("   ⚠️  No audio captured")
            print("   🔍 [DEBUG] audio_buffer is empty")
            return

        print(f"   🔍 [DEBUG] Processing {len(self.audio_buffer)} audio chunks")

        if not self.recognizer:
            print("   ❌ Speech recognizer not available (sr module not loaded)")
            return

        try:
            # Combine audio chunks
            print("   🔍 [DEBUG] Combining audio chunks...")
            combined = np.vstack(self.audio_buffer)
            print(f"   🔍 [DEBUG] Combined audio shape: {combined.shape}")

            audio_data = sr.AudioData(combined.tobytes(), self.sample_rate, 2)
            print(f"   🔍 [DEBUG] Created AudioData object, size: {len(combined.tobytes())} bytes")

            # Transcribe using Google
            print("   🔍 [DEBUG] Calling Google Speech Recognition API...")
            text = self.recognizer.recognize_google(audio_data, language="en-US")

            self.transcription = text
            print(f"   ✅ Transcribed: {text[:100]}...")
            print(f"   🔍 [DEBUG] Full transcription: {text}")

            # Call callback if registered
            if self.on_transcription_complete:
                print("   🔍 [DEBUG] Calling transcription callback...")
                self.on_transcription_complete(text)
                print("   ✅ [DEBUG] Callback completed")
            else:
                print("   ⚠️  [DEBUG] No transcription callback registered")

        except sr.UnknownValueError:
            print("   ⚠️  Could not understand audio")
            print("   🔍 [DEBUG] Speech Recognition could not parse the audio")
            self.transcription = None
        except sr.RequestError as e:
            print(f"   ⚠️  API error: {e}")
            print(f"   🔍 [DEBUG] Request to Google API failed: {e}")
            self.transcription = None
        except Exception as e:
            print(f"   ❌ Transcription error: {e}")
            print("   🔍 [DEBUG] Traceback:")
            import traceback
            traceback.print_exc()
            self.transcription = None

        print("   🔍 [DEBUG] _transcribe() thread finished")

    def get_transcription(self) -> Optional[str]:
        """Get the transcription result"""
        return self.transcription

    def is_busy(self) -> bool:
        """Check if recording or transcribing"""
        return self.is_recording
