"""
Hotkey Listener
Global keyboard hook for detecting hotkey combinations
"""

from pynput import keyboard
from typing import Dict, Callable
import threading


class HotkeyListener:
    """Listens for global hotkey combinations"""

    def __init__(self, hotkeys: Dict[str, str], callback: Callable[[str], None]):
        """
        Initialize hotkey listener

        Args:
            hotkeys: Dictionary of {pynput_hotkey: normalized_hotkey}
                    e.g., {'<ctrl>+<alt>+v': 'CTRL+ALT+V'}
            callback: Function to call when hotkey is pressed
                     Receives normalized hotkey as argument
        """
        self.hotkeys = hotkeys
        self.callback = callback
        self.listener = None
        self._running = False

    def start(self):
        """Start listening for hotkeys"""
        if self._running:
            print("⚠️  Hotkey listener already running")
            return

        print("\n🎹 Starting hotkey listener...")
        print("   Registered hotkeys:")
        for pynput_key, normalized_key in self.hotkeys.items():
            print(f"      • {normalized_key}")

        # Create global hotkeys listener
        self.listener = keyboard.GlobalHotKeys(
            {hotkey: lambda h=normalized: self._on_hotkey(h)
             for hotkey, normalized in self.hotkeys.items()}
        )

        self._running = True
        self.listener.start()

        print("   ✅ Hotkey listener active!")

    def stop(self):
        """Stop listening for hotkeys"""
        if not self._running:
            return

        print("\n🛑 Stopping hotkey listener...")
        if self.listener:
            self.listener.stop()
            self._running = False

        print("   ✅ Hotkey listener stopped")

    def _on_hotkey(self, normalized_hotkey: str):
        """
        Called when a hotkey is pressed

        Args:
            normalized_hotkey: Normalized hotkey string
        """
        if self.callback:
            # Run callback in separate thread to avoid blocking
            thread = threading.Thread(
                target=self.callback,
                args=(normalized_hotkey,),
                daemon=True
            )
            thread.start()

    def is_running(self) -> bool:
        """Check if listener is running"""
        return self._running

    def wait(self):
        """Wait for listener to finish (blocks until stop() is called)"""
        if self.listener:
            self.listener.join()


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing hotkey listener...")
    print("=" * 60)

    def test_callback(hotkey: str):
        print(f"\n🎉 Hotkey pressed: {hotkey}")

    test_hotkeys = {
        '<ctrl>+<alt>+v': 'CTRL+ALT+V',
        '<ctrl>+<alt>+d': 'CTRL+ALT+D',
    }

    listener = HotkeyListener(test_hotkeys, test_callback)
    listener.start()

    print("\n💡 Press CTRL+ALT+V or CTRL+ALT+D to test")
    print("   Press Ctrl+C to exit\n")

    try:
        listener.wait()
    except KeyboardInterrupt:
        listener.stop()
        print("\n✅ Hotkey listener test complete!")
