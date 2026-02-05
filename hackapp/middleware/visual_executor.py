"""
Visual Workflow Executor
Executes visual workflows step-by-step with REAL screen automation (NO MOCKS)
"""

import time
from typing import Dict, Any, Optional
from pathlib import Path


class WorkflowExecutor:
    """Execute visual workflows with real implementations"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}

    def execute(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete visual workflow

        Args:
            workflow: VisualWorkflow dict

        Returns:
            Execution result with status and variables
        """
        self.variables = {}
        results = []
        start_time = time.time()

        try:
            for step in workflow["steps"]:
                if not step.get("enabled", True):
                    continue

                step_result = self._execute_step(step)
                results.append(step_result)

                if step_result["status"] == "error":
                    return {
                        "status": "error",
                        "error": step_result.get("error"),
                        "step_id": step["step_id"],
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "variables": self.variables
                    }

            return {
                "status": "success",
                "steps": results,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "variables": self.variables
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "variables": self.variables
            }

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        step_type = step["step_type"]

        try:
            if step_type == "read_coords":
                return self._read_coords(step)
            elif step_type == "lookup_excel":
                return self._lookup_excel(step)
            elif step_type == "lookup_db":
                return self._lookup_db(step)
            elif step_type == "lookup_api":
                return self._lookup_api(step)
            elif step_type == "write_coords":
                return self._write_coords(step)
            elif step_type == "speech_to_text":
                return self._speech_to_text(step)
            else:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"Unknown step type: {step_type}"
                }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": str(e)
            }

    def _read_coords(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Read text from screen coordinates using OCR - REAL IMPLEMENTATION"""
        try:
            import pyautogui
            from PIL import Image
            import pytesseract
            import os
        except ImportError as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Missing dependency: {str(e)}. Install: pip install pyautogui pillow pytesseract"
            }

        try:
            x = step["x"]
            y = step["y"]
            width = step.get("width", 300)  # Increased from 200
            height = step.get("height", 50)  # Increased from 30
            output_var = step["output_variable"]

            # Small delay to ensure window is ready
            time.sleep(0.2)

            # Screenshot the region
            screenshot = pyautogui.screenshot(region=(x, y, width, height))

            # DEBUG: Save screenshot to see what OCR is reading
            debug_path = "ocr_debug.png"
            screenshot.save(debug_path)
            print(f"   🔍 DEBUG: OCR screenshot saved to {debug_path}")
            print(f"   📍 Coordinates: ({x}, {y}), Size: {width}x{height}")

            # OCR to extract text
            text = pytesseract.image_to_string(screenshot).strip()

            print(f"   📝 OCR Result: '{text}'")

            if not text:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"No text found at coordinates ({x}, {y}). Check ocr_debug.png to see what was captured."
                }

            # Store in variables
            self.variables[output_var] = text

            return {
                "step_id": step["step_id"],
                "status": "success",
                "output": {output_var: text}
            }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"OCR failed: {str(e)}"
            }

    def _lookup_excel(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup data in Excel file - REAL IMPLEMENTATION"""
        try:
            import pandas as pd
        except ImportError:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": "pandas not installed. Install: pip install pandas openpyxl"
            }

        try:
            file_path = Path(step["file_path"])

            # Check if file exists
            if not file_path.exists():
                # Try as absolute path or relative to current dir
                if not Path(file_path.name).exists():
                    return {
                        "step_id": step["step_id"],
                        "status": "error",
                        "error": f"Excel file not found: {file_path}. Please provide full path."
                    }
                file_path = Path(file_path.name)

            sheet_name = step.get("sheet_name", 0)
            search_column = step["search_column"]
            search_value_var = step["search_value_variable"]
            return_columns = step["return_columns"]
            output_var = step["output_variable"]

            # Get search value from variables
            if search_value_var not in self.variables:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"Variable '{search_value_var}' not found. Did you run previous steps?"
                }

            search_value = self.variables[search_value_var]

            # Read Excel
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Search for row
            mask = df[search_column].astype(str).str.contains(str(search_value), case=False, na=False)
            matching_rows = df[mask]

            if matching_rows.empty:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"No match found for '{search_value}' in column '{search_column}'"
                }

            # Get first match
            row = matching_rows.iloc[0]

            # Extract return columns
            result = {}
            for col in return_columns:
                if col in df.columns:
                    result[col] = str(row[col])
                else:
                    return {
                        "step_id": step["step_id"],
                        "status": "error",
                        "error": f"Column '{col}' not found in Excel. Available: {list(df.columns)}"
                    }

            # Store in variables
            self.variables[output_var] = result

            return {
                "step_id": step["step_id"],
                "status": "success",
                "output": {output_var: result}
            }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Excel lookup failed: {str(e)}"
            }

    def _lookup_db(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Lookup data in database - NOT IMPLEMENTED YET"""
        return {
            "step_id": step["step_id"],
            "status": "error",
            "error": "Database lookup not implemented yet. Use Excel for now."
        }

    def _lookup_api(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Call external API - NOT IMPLEMENTED YET"""
        return {
            "step_id": step["step_id"],
            "status": "error",
            "error": "API call not implemented yet. Use Excel for now."
        }

    def _write_coords(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Write text to screen coordinates - REAL IMPLEMENTATION"""
        try:
            import pyautogui
            import pyperclip
        except ImportError as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Missing dependency: {str(e)}. Install: pip install pyautogui pyperclip"
            }

        try:
            x = step["x"]
            y = step["y"]
            content_template = step["content_template"]
            insert_method = step.get("insert_method", "paste")
            key_sequence = step.get("key_sequence", "")  # e.g., "tab,tab,enter"

            # Render template with variables
            content = self._render_template(content_template)

            # Click coordinates
            pyautogui.click(x, y)
            time.sleep(0.3)

            # Insert content
            if insert_method == "paste":
                pyperclip.copy(content)
                pyautogui.hotkey('ctrl', 'v')
            else:
                pyautogui.write(content, interval=0.05)

            time.sleep(0.2)

            # Execute key sequence if provided
            if key_sequence:
                keys = [k.strip().lower() for k in key_sequence.split(',')]
                for key in keys:
                    if key:
                        pyautogui.press(key)
                        time.sleep(0.1)

            return {
                "step_id": step["step_id"],
                "status": "success",
                "output": {"content": content, "key_sequence": key_sequence}
            }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Write failed: {str(e)}"
            }

    def _speech_to_text(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Speech-to-text - NOT IMPLEMENTED IN EXECUTOR"""
        return {
            "step_id": step["step_id"],
            "status": "error",
            "error": "Speech-to-text not available in executor. Use the speech_app separately."
        }

    def _render_template(self, template: str) -> str:
        """Render template with variables using simple {key} or {key.subkey} syntax"""
        import re

        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split('.')

            value = self.variables
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return f"{{UNDEFINED:{var_path}}}"

            return str(value)

        # Replace {variable} and {variable.key} patterns
        result = re.sub(r'\{([a-zA-Z0-9_.]+)\}', replace_var, template)
        return result
