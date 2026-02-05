"""
Coordinate Picker Overlay
Fullscreen crosshair overlay for visual coordinate selection
"""

import tkinter as tk
from typing import Optional, Callable, Tuple


class CoordinatePicker:
    """Fullscreen overlay for picking screen coordinates"""

    def __init__(self, on_coordinate_selected: Callable[[int, int], None]):
        """
        Initialize coordinate picker

        Args:
            on_coordinate_selected: Callback function(x, y) called when user clicks
        """
        self.on_coordinate_selected = on_coordinate_selected
        self.window: Optional[tk.Tk] = None
        self.is_active = False

    def activate(self):
        """Show the picker overlay"""
        if self.is_active:
            return

        self.is_active = True

        # Create fullscreen window
        self.window = tk.Tk()
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-alpha', 0.3)  # Semi-transparent
        self.window.attributes('-topmost', True)
        self.window.config(cursor='crosshair')
        self.window.config(bg='black')

        # Add instruction label
        label = tk.Label(
            self.window,
            text="Click anywhere to capture coordinates\nPress ESC to cancel",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='black'
        )
        label.pack(expand=True)

        # Bind click and ESC
        self.window.bind('<Button-1>', self._on_click)
        self.window.bind('<Escape>', self._on_cancel)

        # Center the window
        self.window.update_idletasks()

        # Start event loop
        self.window.mainloop()

    def _on_click(self, event):
        """Handle mouse click"""
        # Get absolute screen coordinates
        x = self.window.winfo_pointerx()
        y = self.window.winfo_pointery()

        # Close window
        self._close()

        # Callback with coordinates
        if self.on_coordinate_selected:
            self.on_coordinate_selected(x, y)

    def _on_cancel(self, event):
        """Handle ESC key"""
        self._close()

    def _close(self):
        """Close the picker window"""
        if self.window:
            self.window.quit()
            self.window.destroy()
            self.window = None
        self.is_active = False


def pick_coordinates(callback: Callable[[int, int], None]):
    """
    Show coordinate picker and call callback with selected coordinates

    Args:
        callback: Function(x, y) to call with selected coordinates
    """
    picker = CoordinatePicker(on_coordinate_selected=callback)
    picker.activate()


# Test function
if __name__ == "__main__":
    def on_picked(x, y):
        print(f"Coordinates selected: ({x}, {y})")

    pick_coordinates(on_picked)
