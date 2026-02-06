"""
Recording Indicator - Visual feedback for voice recording
Shows a sleek recording indicator overlay when recording is active
"""

import threading
import time
from typing import Optional

try:
    import tkinter as tk
    from tkinter import font
    # Test if display is available (important for WSL2)
    try:
        test_root = tk.Tk()
        test_root.destroy()
        TKINTER_AVAILABLE = True
    except Exception as e:
        TKINTER_AVAILABLE = False
        if "DISPLAY" in str(e) or "display" in str(e).lower():
            # WSL2 without display server
            pass  # Silently skip - common in WSL2
        else:
            print(f"⚠️  tkinter display not available: {e}")
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️  tkinter not available - recording indicator disabled")


class RecordingIndicator:
    """Displays a sleek recording indicator overlay when recording is active"""

    def __init__(self, width: int = 120, height: int = 36, position: str = "top-right"):
        """
        Initialize the recording indicator

        Args:
            width: Width of the indicator in pixels
            height: Height of the indicator in pixels
            position: Where to place the indicator ("top-right", "top-left", "bottom-right", "bottom-left")
        """
        self.width = width
        self.height = height
        self.position = position
        self.window: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.is_showing = False
        self.flash_thread: Optional[threading.Thread] = None
        self.stop_flashing = False
        self.dot_visible = True  # For flashing animation

        if not TKINTER_AVAILABLE:
            self.enabled = False
        else:
            self.enabled = True

    def show(self):
        """Show the recording indicator and start flashing"""
        if not self.enabled or self.is_showing:
            return

        self.is_showing = True
        self.stop_flashing = False

        # Create window in main thread
        threading.Thread(target=self._create_window, daemon=True).start()

    def hide(self):
        """Hide the recording indicator"""
        if not self.enabled or not self.is_showing:
            return

        self.is_showing = False
        self.stop_flashing = True

        # Destroy window
        if self.window:
            try:
                self.window.after(0, self._destroy_window)
            except:
                pass

    def _create_window(self):
        """Create the overlay window (runs in separate thread)"""
        try:
            # Create root window
            self.window = tk.Tk()
            self.window.title("Recording")

            # Set window size
            self.window.geometry(f"{self.width}x{self.height}")

            # Position based on preference
            self._position_window()

            # Configure window properties
            self.window.overrideredirect(True)  # Remove window decorations
            self.window.attributes("-topmost", True)  # Always on top

            # Set background color for transparency
            bg_color = "#1a1a1a"  # Dark background
            self.window.configure(bg=bg_color)

            # Create canvas for drawing
            self.canvas = tk.Canvas(
                self.window,
                width=self.width,
                height=self.height,
                bg=bg_color,
                highlightthickness=0
            )
            self.canvas.pack()

            # Draw rounded rectangle background
            corner_radius = 6
            self._draw_rounded_rectangle(
                4, 4, self.width - 4, self.height - 4,
                corner_radius,
                fill="#2d2d2d",
                outline="#404040",
                width=1
            )

            # Draw red recording dot (left side)
            dot_x = 16
            dot_y = self.height // 2
            dot_radius = 6
            self.rec_dot = self.canvas.create_oval(
                dot_x - dot_radius,
                dot_y - dot_radius,
                dot_x + dot_radius,
                dot_y + dot_radius,
                fill="#ff3333",
                outline="#cc0000",
                width=1
            )

            # Add "REC" text
            text_font = ("Segoe UI", 9, "bold")
            self.rec_text = self.canvas.create_text(
                self.width // 2 + 8,
                self.height // 2,
                text="RECORDING",
                fill="#ffffff",
                font=text_font
            )

            # Start flashing animation
            self._flash_animation()

            # Run the window
            self.window.mainloop()

        except Exception as e:
            print(f"   ⚠️  Could not create recording indicator: {e}")
            self.is_showing = False

    def _draw_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle on the canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]

        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _position_window(self):
        """Position the window based on preference"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        margin = 20

        if self.position == "top-right":
            x = screen_width - self.width - margin
            y = margin
        elif self.position == "top-left":
            x = margin
            y = margin
        elif self.position == "bottom-right":
            x = screen_width - self.width - margin
            y = screen_height - self.height - margin
        elif self.position == "bottom-left":
            x = margin
            y = screen_height - self.height - margin
        else:
            # Default to top-right
            x = screen_width - self.width - margin
            y = margin

        self.window.geometry(f"+{x}+{y}")

    def _flash_animation(self):
        """Animate the red dot flashing"""
        if not self.is_showing or self.stop_flashing:
            return

        try:
            # Toggle dot visibility
            self.dot_visible = not self.dot_visible

            if self.dot_visible:
                # Bright red when visible
                self.canvas.itemconfig(self.rec_dot, fill="#ff3333", outline="#cc0000")
            else:
                # Dim red when "off"
                self.canvas.itemconfig(self.rec_dot, fill="#661111", outline="#440000")

            # Schedule next flash (600ms for smooth pulsing)
            self.window.after(600, self._flash_animation)

        except Exception as e:
            # Window might be destroyed
            pass

    def _destroy_window(self):
        """Destroy the window safely"""
        try:
            if self.window:
                self.window.quit()
                self.window.destroy()
                self.window = None
                self.canvas = None
        except:
            pass


# Global instance for easy access
_indicator: Optional[RecordingIndicator] = None


def get_indicator() -> RecordingIndicator:
    """Get the global recording indicator instance"""
    global _indicator
    if _indicator is None:
        _indicator = RecordingIndicator(width=120, height=36, position="top-right")
    return _indicator


def show_recording_indicator():
    """Show the recording indicator"""
    get_indicator().show()


def hide_recording_indicator():
    """Hide the recording indicator"""
    get_indicator().hide()
