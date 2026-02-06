"""
Recording Indicator - Visual feedback for voice recording
Shows a sleek flashing indicator overlay when recording is active
"""

import threading
import time
from typing import Optional

try:
    import tkinter as tk
    from tkinter import font
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️  tkinter not available - recording indicator disabled")


class RecordingIndicator:
    """Displays a sleek flashing indicator overlay when recording is active"""

    def __init__(self, width: int = 100, height: int = 35, position: str = "top-right"):
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
        self.flash_state = False

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

            # Platform-specific transparency
            try:
                self.window.wm_attributes("-transparentcolor", "#f0f0f0")
            except:
                pass

            # Create canvas for drawing
            self.canvas = tk.Canvas(
                self.window,
                width=self.width,
                height=self.height,
                bg="#f0f0f0",
                highlightthickness=0
            )
            self.canvas.pack()

            # Draw the indicator components
            self._draw_indicator()

            # Start flashing animation
            self._flash_animation()

            # Run the window
            self.window.mainloop()

        except Exception as e:
            print(f"   ⚠️  Could not create recording indicator: {e}")
            self.is_showing = False

    def _draw_indicator(self):
        """Draw the recording indicator with rounded rectangle and elements"""
        # Rounded rectangle parameters
        radius = 8
        padding = 2

        # Draw rounded rectangle background
        self.bg_rect = self._create_rounded_rectangle(
            padding, padding,
            self.width - padding, self.height - padding,
            radius=radius,
            fill="#DC143C",  # Crimson red
            outline=""
        )

        # Draw small circle (recording dot) on the left
        dot_x = 15
        dot_y = self.height // 2
        dot_radius = 6
        self.dot = self.canvas.create_oval(
            dot_x - dot_radius,
            dot_y - dot_radius,
            dot_x + dot_radius,
            dot_y + dot_radius,
            fill="white",
            outline=""
        )

        # Draw "REC" text
        self.text = self.canvas.create_text(
            self.width // 2 + 10,
            self.height // 2,
            text="REC",
            fill="white",
            font=("Arial", 11, "bold")
        )

    def _create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """Create a rounded rectangle on the canvas"""
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

        return self.canvas.create_polygon(points, **kwargs, smooth=True)

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
        """Animate the indicator flashing"""
        if not self.is_showing or self.stop_flashing:
            return

        try:
            # Toggle flash state
            self.flash_state = not self.flash_state

            if self.flash_state:
                # Bright state
                bg_color = "#DC143C"  # Crimson red
                dot_fill = "white"
            else:
                # Dim state
                bg_color = "#B22222"  # Firebrick (darker red)
                dot_fill = "#FFB6C1"  # Light pink (dimmed white)

            # Update colors
            self.canvas.itemconfig(self.bg_rect, fill=bg_color)
            self.canvas.itemconfig(self.dot, fill=dot_fill)

            # Schedule next flash (600ms for smoother animation)
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
        _indicator = RecordingIndicator(width=100, height=35, position="top-right")
    return _indicator


def show_recording_indicator():
    """Show the recording indicator"""
    get_indicator().show()


def hide_recording_indicator():
    """Hide the recording indicator"""
    get_indicator().hide()
