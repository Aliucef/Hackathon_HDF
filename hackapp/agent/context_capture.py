"""
Context Capture
Captures context when hotkey is pressed
"""

import pyperclip
import sys
from typing import Optional
from datetime import datetime

# Import window management based on platform
if sys.platform.startswith('win'):
    try:
        import pygetwindow as gw
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
        print("⚠️  pygetwindow not available, window detection disabled")
else:
    WINDOWS_AVAILABLE = False


class ContextCapture:
    """Captures context information when hotkey is triggered"""

    def __init__(self, backup_clipboard: bool = True):
        """
        Initialize context capture

        Args:
            backup_clipboard: Whether to backup clipboard before reading
        """
        self.backup_clipboard = backup_clipboard
        self._clipboard_backup = None

    def get_active_window_title(self) -> Optional[str]:
        """
        Get the title of the currently active window

        Returns:
            Window title or None if unavailable
        """
        if not WINDOWS_AVAILABLE:
            return None

        try:
            active_window = gw.getActiveWindow()
            if active_window:
                return active_window.title
        except Exception as e:
            print(f"⚠️  Could not get active window: {e}")

        return None

    def get_clipboard_text(self) -> Optional[str]:
        """
        Get text from clipboard

        Returns:
            Clipboard text or None if unavailable
        """
        try:
            # Backup current clipboard if requested
            if self.backup_clipboard:
                self._clipboard_backup = pyperclip.paste()

            return pyperclip.paste()
        except Exception as e:
            print(f"⚠️  Could not access clipboard: {e}")
            return None

    def restore_clipboard(self):
        """Restore previously backed up clipboard content"""
        if self._clipboard_backup is not None:
            try:
                pyperclip.copy(self._clipboard_backup)
                self._clipboard_backup = None
            except Exception as e:
                print(f"⚠️  Could not restore clipboard: {e}")

    def capture(self, hotkey: str, user_id: Optional[str] = None) -> dict:
        """
        Capture full context

        Args:
            hotkey: The hotkey that was pressed
            user_id: Optional user identifier

        Returns:
            Context dictionary
        """
        # Get window title
        window_title = self.get_active_window_title()

        # Get clipboard/selected text
        # Note: We assume user selected text before pressing hotkey,
        # so clipboard contains the selection
        selected_text = self.get_clipboard_text()

        context = {
            "hotkey": hotkey,
            "selected_text": selected_text,
            "clipboard_text": selected_text,  # Same as selected_text for now
            "window_title": window_title,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "active_field": None  # Not available without DXCare API
        }

        return context

    def is_dxcare_active(self, dxcare_keywords: list) -> bool:
        """
        Check if DXCare window is currently active

        Args:
            dxcare_keywords: List of keywords that identify DXCare

        Returns:
            True if DXCare appears to be active
        """
        window_title = self.get_active_window_title()

        if not window_title:
            return False

        # Check if any keyword is in window title
        return any(keyword.lower() in window_title.lower() for keyword in dxcare_keywords)


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing context capture...")
    print("=" * 60)

    capturer = ContextCapture()

    print("\n1. Active Window:")
    window = capturer.get_active_window_title()
    print(f"   {window or 'Not available'}")

    print("\n2. Clipboard:")
    clipboard = capturer.get_clipboard_text()
    print(f"   {clipboard[:50] if clipboard else 'Empty'}...")

    print("\n3. Full Context:")
    context = capturer.capture("CTRL+ALT+V", user_id="test_user")
    for key, value in context.items():
        if value and len(str(value)) > 50:
            print(f"   {key}: {str(value)[:50]}...")
        else:
            print(f"   {key}: {value}")

    print("\n✅ Context capture tests complete!")
