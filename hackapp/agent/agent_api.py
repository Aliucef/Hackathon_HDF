"""
Agent API Server
Runs a simple Flask server to receive GUI automation commands from middleware
"""

import time
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import pyautogui
    import pyperclip
    PYAUTOGUI_AVAILABLE = True
except (ImportError, OSError) as e:
    PYAUTOGUI_AVAILABLE = False
    print(f"⚠️  pyautogui not available: {e}")


class AgentAPI:
    """Simple API server for agent to receive GUI commands"""

    def __init__(self, port=5002):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)  # Allow middleware to call from different origin
        self.server_thread = None
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "ok",
                "pyautogui_available": PYAUTOGUI_AVAILABLE
            })

        @self.app.route('/execute/write_coords', methods=['POST'])
        def execute_write_coords():
            """Execute write_coords GUI action"""
            if not PYAUTOGUI_AVAILABLE:
                return jsonify({
                    "status": "error",
                    "error": "pyautogui not available on agent"
                }), 500

            try:
                data = request.json
                x = data.get('x')
                y = data.get('y')
                content = data.get('content')
                insert_method = data.get('insert_method', 'paste')
                key_sequence = data.get('key_sequence', '')

                print(f"   🔍 [AGENT API] VERSION 2.0 - Received write_coords: ({x}, {y}) = {content[:50]}...")

                # Backup clipboard if using paste method
                original_clipboard = None
                if insert_method == "paste":
                    try:
                        original_clipboard = pyperclip.paste()
                    except:
                        pass

                # Click coordinates
                print(f"   🖱️  [AGENT API] Clicking ({x}, {y})")
                print(f"   🔍 [AGENT API] Screen size: {pyautogui.size()}")
                print(f"   🔍 [AGENT API] Current mouse position before click: {pyautogui.position()}")
                pyautogui.click(x, y)
                time.sleep(0.3)
                print(f"   🔍 [AGENT API] Mouse position after click: {pyautogui.position()}")

                # Insert content
                if insert_method == "paste":
                    print(f"   📋 [AGENT API] Copying to clipboard: {content[:50]}...")
                    pyperclip.copy(content)
                    clipboard_check = pyperclip.paste()
                    print(f"   🔍 [AGENT API] Clipboard verify: {clipboard_check[:50]}...")

                    print(f"   ⌨️  [AGENT API] Pressing Ctrl+V")
                    pyautogui.hotkey('ctrl', 'v')
                    time.sleep(0.2)

                    # Restore clipboard
                    if original_clipboard is not None:
                        try:
                            pyperclip.copy(original_clipboard)
                            print(f"   🔍 [AGENT API] Clipboard restored")
                        except:
                            pass
                else:
                    print(f"   ⌨️  [AGENT API] Typing content character by character")
                    pyautogui.write(content, interval=0.05)

                time.sleep(0.2)

                # Execute key sequence if provided
                if key_sequence:
                    print(f"   🔍 [AGENT API] Executing key sequence: {key_sequence}")
                    keys = [k.strip().lower() for k in key_sequence.split(',')]
                    for key in keys:
                        if key:
                            pyautogui.press(key)
                            time.sleep(0.1)

                print(f"   ✅ [AGENT API] Content written successfully")

                return jsonify({
                    "status": "success",
                    "content": content,
                    "coordinates": {"x": x, "y": y}
                })

            except Exception as e:
                print(f"   ❌ [AGENT API] Write error: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    "status": "error",
                    "error": str(e)
                }), 500

    def start(self):
        """Start the API server in background thread"""
        if self.server_thread and self.server_thread.is_alive():
            print(f"   ⚠️  Agent API already running on port {self.port}")
            return

        def run_server():
            print(f"   🚀 Agent API server starting on port {self.port}...")
            self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        time.sleep(1)  # Give server time to start
        print(f"   ✅ Agent API ready on http://localhost:{self.port}")

    def stop(self):
        """Stop the API server (Flask doesn't support graceful shutdown easily)"""
        # Flask in thread doesn't support easy shutdown
        # Will be terminated when main process exits
        pass


# Global instance
_api_server = None


def get_agent_api(port=5002):
    """Get or create the global agent API server"""
    global _api_server
    if _api_server is None:
        _api_server = AgentAPI(port=port)
    return _api_server


def start_agent_api(port=5002):
    """Start the agent API server"""
    api = get_agent_api(port)
    api.start()
    return api
