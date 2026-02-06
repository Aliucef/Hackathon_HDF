"""
Visual Workflow Executor
Executes visual workflows step-by-step with REAL screen automation (NO MOCKS)
"""

import time
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class WorkflowExecutor:
    """Execute visual workflows with real implementations"""

    def __init__(self):
        self.variables: Dict[str, Any] = {}

        # Disable pyautogui failsafe to prevent accidental stops
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            pyautogui.PAUSE = 0.1  # Small pause between actions
        except ImportError:
            pass

    def execute(self, workflow: Dict[str, Any], initial_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a complete visual workflow

        Args:
            workflow: VisualWorkflow dict
            initial_variables: Optional dict of variables to start with (e.g., transcription)

        Returns:
            Execution result with status and variables
        """
        # Reset state for fresh execution, but include initial variables
        self.variables = initial_variables.copy() if initial_variables else {}
        results = []
        start_time = time.time()

        try:
            # Ensure pyautogui is in clean state
            try:
                import pyautogui
                # Reset any held keys/buttons
                pyautogui.FAILSAFE = False
            except:
                pass

            for step in workflow["steps"]:
                if not step.get("enabled", True):
                    continue

                step_result = self._execute_step(step)
                results.append(step_result)

                if step_result["status"] == "error":
                    # Clean up on error
                    self._cleanup_resources()
                    return {
                        "status": "error",
                        "error": step_result.get("error"),
                        "step_id": step["step_id"],
                        "execution_time_ms": int((time.time() - start_time) * 1000),
                        "variables": self.variables
                    }

            # Clean up after successful execution
            self._cleanup_resources()

            return {
                "status": "success",
                "steps": results,
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "variables": self.variables
            }

        except Exception as e:
            # Clean up on unexpected error
            self._cleanup_resources()
            print(f"   ❌ Unexpected execution error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "variables": self.variables
            }

    def _cleanup_resources(self):
        """Clean up any held resources to prepare for next execution"""
        try:
            import pyautogui
            # Release any held keys
            pyautogui.keyUp('ctrl')
            pyautogui.keyUp('alt')
            pyautogui.keyUp('shift')
        except:
            pass

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
            elif step_type == "format_with_llm":
                return self._format_with_llm(step)
            elif step_type == "write_coords":
                return self._write_coords(step)
            elif step_type == "record_audio":
                return self._record_audio(step)
            elif step_type == "transcribe_audio":
                return self._transcribe_audio(step)
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
            import re
        except ImportError as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Missing dependency: {str(e)}. Install: pip install pyautogui pillow pytesseract"
            }

        try:
            x = step["x"]
            y = step["y"]
            width = step.get("width", 150)  # Smaller width for patient ID
            height = step.get("height", 40)  # Smaller height
            output_var = step["output_variable"]
            extract_numbers = step.get("extract_numbers", True)  # New: Extract only numbers

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

            print(f"   📝 OCR Raw Result: '{text}'")

            if not text:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"No text found at coordinates ({x}, {y}). Check ocr_debug.png to see what was captured."
                }

            # Extract only numbers if requested (for patient IDs)
            if extract_numbers:
                # Find first sequence of digits (patient ID)
                numbers = re.findall(r'\d+', text)
                if numbers:
                    text = numbers[0]  # Take first number sequence
                    print(f"   🔢 Extracted Patient ID: '{text}'")
                else:
                    return {
                        "step_id": step["step_id"],
                        "status": "error",
                        "error": f"No numbers found in OCR text: '{text}'. Check ocr_debug.png."
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

            # Read Excel with explicit file handle management
            # Use ExcelFile context manager to ensure proper cleanup
            with pd.ExcelFile(file_path, engine='openpyxl') as xls:
                df = pd.read_excel(xls, sheet_name=sheet_name)

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

            print(f"   ✅ Excel lookup successful: found {len(result)} fields")

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
        """Write text to screen coordinates - delegates to agent API"""
        try:
            import requests
        except ImportError:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": "requests library not available"
            }

        try:
            x = step["x"]
            y = step["y"]
            content_template = step["content_template"]
            insert_method = step.get("insert_method", "paste")
            key_sequence = step.get("key_sequence", "")

            # Render template with variables
            print(f"   📝 Rendering template: {content_template[:100]}...")
            content = self._render_template(content_template)
            print(f"   📝 Rendered content: {content[:100]}...")

            if not content or content.startswith("{UNDEFINED:"):
                print(f"   ⚠️  WARNING: Template rendering failed - content is undefined")
                print(f"   Available variables: {list(self.variables.keys())}")

            # Send to agent API for execution
            print(f"   🖱️  Sending write command to agent: ({x}, {y})")

            agent_url = "http://localhost:5002/execute/write_coords"
            payload = {
                "x": x,
                "y": y,
                "content": content,
                "insert_method": insert_method,
                "key_sequence": key_sequence
            }

            try:
                response = requests.post(agent_url, json=payload, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Content written to ({x}, {y}): {content[:50]}...")
                    return {
                        "step_id": step["step_id"],
                        "status": "success",
                        "output": {"content": content, "key_sequence": key_sequence}
                    }
                else:
                    error_msg = response.json().get('error', 'Unknown error')
                    print(f"   ❌ Agent returned error: {error_msg}")
                    return {
                        "step_id": step["step_id"],
                        "status": "error",
                        "error": f"Agent error: {error_msg}"
                    }

            except requests.exceptions.ConnectionError:
                print(f"   ❌ Cannot connect to agent API on port 5002")
                print(f"   💡 Make sure agent is running and API server started")
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": "Cannot connect to agent API. Is agent running?"
                }
            except requests.exceptions.Timeout:
                print(f"   ❌ Agent API timeout")
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": "Agent API timeout"
                }

        except Exception as e:
            print(f"   ❌ Write error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Write failed: {str(e)}"
            }

    def _format_with_llm(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Format data using Gemini LLM based on field descriptions"""
        try:
            import requests
        except ImportError:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": "requests not installed. Install: pip install requests"
            }

        try:
            # Use hardcoded API key (secure - not exposed in frontend)
            api_key = GROQ_API_KEY

            input_variable = step.get("input_variable")
            fields = step.get("fields", [])  # List of {name, description}
            output_variable = step.get("output_variable", "formatted_fields")

            if input_variable not in self.variables:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"Variable '{input_variable}' not found"
                }

            # Get input data
            input_data = self.variables[input_variable]

            # Build prompt for LLM
            prompt = self._build_llm_prompt(input_data, fields)

            # Call Groq API (fast and free!)
            url = "https://api.groq.com/openai/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "llama-3.3-70b-versatile",  # Fast Groq model
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }

            print(f"   🤖 Calling Groq LLM to format {len(fields)} fields...")

            response = requests.post(url, headers=headers, json=payload, timeout=15)

            if not response.ok:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": f"Groq API error: {response.status_code} - {response.text}"
                }

            result = response.json()

            # Extract generated text (OpenAI-compatible format)
            if "choices" not in result or len(result["choices"]) == 0:
                return {
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": "No response from Groq"
                }

            generated_text = result["choices"][0]["message"]["content"]

            print(f"   ✅ LLM Response received")
            print(f"   📄 Raw LLM output: {generated_text[:200]}...")

            # Parse LLM output into field values
            formatted_fields = self._parse_llm_output(generated_text, fields)

            print(f"   📊 Formatted fields: {formatted_fields}")

            # Store in variables
            self.variables[output_variable] = formatted_fields

            return {
                "step_id": step["step_id"],
                "status": "success",
                "output": {output_variable: formatted_fields}
            }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"LLM formatting failed: {str(e)}"
            }

    def _build_llm_prompt(self, input_data: Any, fields: list) -> str:
        """Build prompt for Gemini to format data into fields"""
        prompt = "You are a medical data formatter. Given patient data, format it for specific fields.\n\n"
        prompt += "INPUT DATA:\n"

        if isinstance(input_data, dict):
            for key, value in input_data.items():
                prompt += f"- {key}: {value}\n"
        else:
            prompt += str(input_data) + "\n"

        prompt += "\nFIELDS TO FILL:\n"
        for i, field in enumerate(fields, 1):
            prompt += f"{i}. {field['name']}: {field['description']}\n"

        prompt += "\nINSTRUCTIONS:\n"
        prompt += "- Format the data appropriately for each field\n"
        prompt += "- Keep it concise and clinical\n"
        prompt += "- Use the exact field names in your response\n"
        prompt += "- Format your response EXACTLY like this:\n\n"

        for field in fields:
            prompt += f"[{field['name']}]\n<content for this field>\n\n"

        prompt += "Do NOT include any other text or explanations."

        return prompt

    def _parse_llm_output(self, llm_output: str, fields: list) -> dict:
        """Parse LLM output into field values"""
        import re

        result = {}

        for field in fields:
            field_name = field['name']

            # Try format 1: [field_name]\ncontent
            pattern1 = rf'\[{re.escape(field_name)}\]\s*\n(.*?)(?:\n\[|$)'
            match = re.search(pattern1, llm_output, re.DOTALL)

            if match:
                content = match.group(1).strip()
                result[field_name] = content
            else:
                # Try format 2: field_name\ncontent (without brackets)
                # Match field name at line start, then capture until next capital letter or end
                pattern2 = rf'(?:^|\n){re.escape(field_name)}\s*\n(.*?)(?:\n[A-Z]|$)'
                match = re.search(pattern2, llm_output, re.DOTALL | re.MULTILINE)

                if match:
                    content = match.group(1).strip()
                    result[field_name] = content
                else:
                    # Fallback: just use empty string
                    print(f"   ⚠️  Could not parse field '{field_name}' from LLM output")
                    result[field_name] = ""

        return result

    def _record_audio(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record audio - PLACEHOLDER

        Note: Actual recording is handled by agent toggle state.
        This step exists for workflow definition but recording happens externally.
        """
        output_var = step.get("output_variable", "audio_file")

        # For now, just indicate that audio recording is handled by agent
        print(f"   🎤 Audio recording (handled by agent toggle)")

        # Store placeholder - actual audio is managed by agent state
        self.variables[output_var] = "audio_recorded"

        return {
            "step_id": step["step_id"],
            "status": "success",
            "output": {output_var: "audio_recorded"}
        }

    def _transcribe_audio(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Transcribe audio to text - uses pre-provided transcription from agent"""
        try:
            output_variable = step.get("output_variable", "transcription")

            # Check if transcription was passed as initial variable (from agent)
            if "transcription" in self.variables:
                transcription = self.variables["transcription"]

                print(f"   ✅ Using transcription from agent: {transcription[:100]}...")

                # Store in output variable if different
                if output_variable != "transcription":
                    self.variables[output_variable] = transcription

                return {
                    "step_id": step["step_id"],
                    "status": "success",
                    "output": {output_variable: transcription}
                }

            # No transcription available
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": "No transcription available. Make sure agent provided transcription as initial variable."
            }

        except Exception as e:
            return {
                "step_id": step["step_id"],
                "status": "error",
                "error": f"Transcription failed: {str(e)}"
            }

    def _speech_to_text(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Speech-to-text - DEPRECATED, use _transcribe_audio instead"""
        return self._transcribe_audio(step)

    def _render_template(self, template: str) -> str:
        """Render template with variables using simple {key} or {key.subkey} syntax"""
        import re

        def replace_var(match):
            var_path = match.group(1)
            parts = var_path.split('.')

            value = self.variables
            for part in parts:
                # Strip spaces from part for lookup
                part = part.strip()
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return f"{{UNDEFINED:{var_path}}}"

            return str(value)

        # Replace {variable} and {variable.key} patterns (now allows spaces in keys)
        result = re.sub(r'\{([a-zA-Z0-9_. ]+)\}', replace_var, template)
        return result
