"""
HackApp Coordinate Picker

Pick where the agent should click in DXCare before pasting text.
Saves the picked coordinates directly into workflows.yaml.

Run:  python tools/coord_picker.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# ---------------------------------------------------------------------------
# Path to workflows.yaml — works whether you run from hackapp/ or tools/
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
WORKFLOWS_PATH = os.path.abspath(os.path.join(_HERE, "..", "config", "workflows.yaml"))


# ---------------------------------------------------------------------------
# YAML loader (only for the dropdown; we do NOT use yaml.dump to write back
# so that comments and formatting in the file are preserved)
# ---------------------------------------------------------------------------

def _load_workflow_names():
    """Return list of (workflow_id, name) from workflows.yaml."""
    try:
        import yaml
        with open(WORKFLOWS_PATH, "r") as f:
            config = yaml.safe_load(f)
        return [(w.get("workflow_id", "?"), w.get("name", "?"))
                for w in config.get("workflows", [])]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Coordinate Picker App
# ---------------------------------------------------------------------------

class CoordPicker:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HackApp – Coordinate Picker")
        self.root.geometry("420x340")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.picked_x = None
        self.picked_y = None
        self.overlay = None

        # Workflow list: [(id, name), ...]
        self.workflows = _load_workflow_names()

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#181825", pady=14)
        header.pack(fill="x")
        tk.Label(header, text="🎯  Field Coordinate Picker",
                 font=("Helvetica", 16, "bold"),
                 fg="white", bg="#181825").pack()

        # Body
        body = tk.Frame(self.root, bg="#1e1e2e")
        body.pack(fill="both", expand=True, padx=22, pady=10)

        tk.Label(body,
                 text="Pick where the agent should click before pasting text into DXCare.",
                 font=("Helvetica", 9), fg="#a6adc8", bg="#1e1e2e",
                 wraplength=370, justify="left").pack(pady=(0, 14))

        # Workflow selector
        row = tk.Frame(body, bg="#1e1e2e")
        row.pack(fill="x", pady=(0, 10))
        tk.Label(row, text="Workflow:", font=("Helvetica", 10),
                 fg="#cdd6f4", bg="#1e1e2e", width=10, anchor="w").pack(side="left")

        self.wf_var = tk.StringVar()
        display_names = [name for _, name in self.workflows]
        self.wf_dropdown = ttk.Combobox(row, textvariable=self.wf_var,
                                        values=display_names,
                                        state="readonly", width=34)
        if display_names:
            self.wf_dropdown.current(0)
        self.wf_dropdown.pack(side="left")

        # Picked coordinates display
        self.coords_var = tk.StringVar(value="No coordinates picked yet")
        tk.Label(body, textvariable=self.coords_var,
                 font=("Consolas", 14, "bold"),
                 fg="#cba6f7", bg="#1e1e2e").pack(pady=(12, 10))

        # Pick button
        self.pick_btn = tk.Button(
            body, text="🎯  Pick Field Location",
            font=("Helvetica", 11, "bold"),
            bg="#89b4fa", fg="#1e1e2e", activebackground="#74c7ec",
            relief="flat", bd=0, padx=18, pady=7,
            command=self.start_picking, cursor="hand2"
        )
        self.pick_btn.pack(pady=(0, 8))

        # Save button (disabled until coords are picked)
        self.save_btn = tk.Button(
            body, text="💾  Save to workflows.yaml",
            font=("Helvetica", 10),
            bg="#a6e3a1", fg="#1e1e2e", activebackground="#94e2c4",
            relief="flat", bd=0, padx=14, pady=5,
            command=self.save_coords, state="disabled", cursor="hand2"
        )
        self.save_btn.pack(pady=(0, 6))

        # Status line
        self.status_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.status_var,
                 font=("Helvetica", 9), fg="#a6e3a1", bg="#1e1e2e").pack(pady=(4, 0))

    # ------------------------------------------------------------------
    # Picking
    # ------------------------------------------------------------------

    def start_picking(self):
        """Hide this window, show a semi-transparent fullscreen overlay."""
        self.pick_btn.config(state="disabled")
        self.root.withdraw()

        self.overlay = tk.Toplevel()
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.25)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="black", cursor="crosshair")

        tk.Label(self.overlay, text="Click on the target field in DXCare",
                 font=("Helvetica", 22, "bold"), fg="white", bg="black").pack(pady=70)
        tk.Label(self.overlay, text="(this dark overlay covers the whole screen)",
                 font=("Helvetica", 11), fg="#aaa", bg="black").pack()

        self.overlay.bind("<Button-1>", self._on_screen_click)

    def _on_screen_click(self, event):
        """Capture the click, close overlay, restore main window."""
        self.picked_x = event.x_root
        self.picked_y = event.y_root

        self.overlay.destroy()
        self.overlay = None
        self.root.deiconify()

        self.coords_var.set(f"x = {self.picked_x},   y = {self.picked_y}")
        self.pick_btn.config(state="normal")
        self.save_btn.config(state="normal")
        self.status_var.set("")

    # ------------------------------------------------------------------
    # Saving  (line-based rewrite — preserves all comments)
    # ------------------------------------------------------------------

    def save_coords(self):
        selected_name = self.wf_var.get()
        if not selected_name:
            messagebox.showwarning("No workflow", "Select a workflow first.")
            return

        try:
            with open(WORKFLOWS_PATH, "r") as f:
                lines = f.readlines()

            new_value = f"{self.picked_x},{self.picked_y}"

            # Walk through lines: once we see the target workflow name we are
            # "inside" it.  The first click_before we hit after that gets
            # rewritten.  A new "- workflow_id:" resets the flag.
            in_target = False
            saved = False
            new_lines = []

            for line in lines:
                # New workflow boundary
                if line.strip().startswith("- workflow_id:"):
                    in_target = False

                # Workflow name match
                if "name:" in line and selected_name in line:
                    in_target = True

                # Rewrite click_before inside the target workflow
                if in_target and not saved and "click_before:" in line:
                    indent = len(line) - len(line.lstrip())
                    line = " " * indent + f'click_before: "{new_value}"\n'
                    saved = True
                    in_target = False  # done

                new_lines.append(line)

            if not saved:
                messagebox.showwarning(
                    "click_before not found",
                    f"'{selected_name}' has no click_before field in its output.\n\n"
                    "Add click_before to the workflow in workflows.yaml first."
                )
                return

            with open(WORKFLOWS_PATH, "w") as f:
                f.writelines(new_lines)

            self.status_var.set(f"✅  Saved ({self.picked_x},{self.picked_y}) → {selected_name}")
            self.save_btn.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ------------------------------------------------------------------

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = CoordPicker()
    app.run()
