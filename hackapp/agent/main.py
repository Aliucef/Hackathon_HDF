"""
HackApp Agent - Desktop Client
Main entry point for the agent application
"""

import sys
import threading
from datetime import datetime
from hotkey_listener import HotkeyListener
from context_capture import ContextCapture
from inserter import FieldInserter
from middleware_client import MiddlewareClient, MiddlewareError
from picker import pick_coordinates
import config


class HackAppAgent:
    """Main agent application"""

    def __init__(self):
        print("=" * 70)
        print("🖱️  HackApp Agent - Desktop Client")
        print("=" * 70)

        # Initialize components
        self.middleware_client = MiddlewareClient(
            base_url=config.MIDDLEWARE_URL,
            token=config.MIDDLEWARE_TOKEN,
            timeout=config.REQUEST_TIMEOUT_SECONDS
        )

        self.context_capturer = ContextCapture(
            backup_clipboard=config.BACKUP_CLIPBOARD
        )

        self.inserter = FieldInserter(
            insert_delay_ms=config.INSERT_DELAY_MS
        )

        # Hotkey listener for YAML workflows
        self.hotkey_listener = HotkeyListener(
            hotkeys=config.HOTKEYS,
            callback=self.on_hotkey_pressed
        )

        # Picker hotkey listener
        self.picker_listener = HotkeyListener(
            hotkeys={config.PICKER_HOTKEY: config.PICKER_HOTKEY_DISPLAY},
            callback=self.on_picker_hotkey_pressed
        )

        # Visual workflows hotkey listener (loaded dynamically)
        self.visual_workflow_listener = None
        self.visual_workflows = {}  # Map hotkey -> workflow_id

        # Coordinate picking state
        self.picking_active = False
        self.current_picking_field = None

        print("\n✅ Agent components initialized")

    def start(self):
        """Start the agent"""
        print("\n📡 Checking middleware connection...")

        # Check middleware health
        try:
            if self.middleware_client.health_check():
                print("   ✅ Middleware is online and healthy")
            else:
                print("   ⚠️  Middleware health check failed")
                print(f"   URL: {config.MIDDLEWARE_URL}")

        except Exception as e:
            print(f"   ❌ Cannot connect to middleware: {e}")
            print(f"   URL: {config.MIDDLEWARE_URL}")
            print("\n   Please start the middleware server first:")
            print("   python hackapp/middleware/main.py")
            sys.exit(1)

        # List available YAML workflows
        workflows = self.middleware_client.list_workflows()
        if workflows:
            print(f"\n📋 Loaded {len(workflows)} YAML workflow(s):")
            for wf in workflows:
                print(f"   • {wf['hotkey']}: {wf['name']}")

        # Load visual workflows
        visual_workflows = self.middleware_client.list_visual_workflows()
        if visual_workflows:
            print(f"\n🎨 Loaded {len(visual_workflows)} visual workflow(s):")

            visual_hotkeys = {}
            for wf in visual_workflows:
                if wf.get('enabled') and wf.get('hotkey'):
                    hotkey = wf['hotkey']
                    workflow_id = wf['workflow_id']

                    # Convert to pynput format (e.g., "CTRL+ALT+E" -> "<ctrl>+<alt>+e")
                    pynput_hotkey = self._convert_to_pynput_format(hotkey)
                    visual_hotkeys[pynput_hotkey] = hotkey
                    self.visual_workflows[hotkey] = workflow_id

                    print(f"   • {hotkey}: {wf['name']}")

            # Start visual workflow listener if we have any
            if visual_hotkeys:
                self.visual_workflow_listener = HotkeyListener(
                    hotkeys=visual_hotkeys,
                    callback=self.on_visual_workflow_hotkey_pressed
                )
                self.visual_workflow_listener.start()

        # Start YAML workflow hotkey listener
        self.hotkey_listener.start()

        # Start coordinate picker hotkey listener
        self.picker_listener.start()

        print("\n" + "=" * 70)
        print("✅ HackApp Agent is Ready!")
        print("=" * 70)
        print("\n💡 Usage:")
        print("   📍 Coordinate Picker:")
        print(f"      Press {config.PICKER_HOTKEY_DISPLAY} to pick coordinates on screen")
        print("\n   📋 YAML Workflows:")
        print("      1. Select clinical text in DXCare")
        print("      2. Press workflow hotkey (e.g., CTRL+ALT+V)")
        print("\n   🎨 Visual Workflows:")
        print("      Press configured hotkey (e.g., CTRL+ALT+E) to execute")
        print("\n🛑 Press Ctrl+C to exit")
        print("=" * 70 + "\n")

        # Wait for hotkeys
        try:
            self.hotkey_listener.wait()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the agent"""
        print("\n\n🛑 Shutting down HackApp Agent...")
        self.hotkey_listener.stop()
        self.picker_listener.stop()
        if self.visual_workflow_listener:
            self.visual_workflow_listener.stop()
        print("✅ Agent stopped\n")

    def _convert_to_pynput_format(self, hotkey: str) -> str:
        """
        Convert display hotkey to pynput format
        Example: "CTRL+ALT+E" -> "<ctrl>+<alt>+e"
        """
        parts = hotkey.lower().split('+')
        return '+'.join(f'<{part}>' if part in ['ctrl', 'alt', 'shift'] else part for part in parts)

    def on_picker_hotkey_pressed(self, hotkey: str):
        """Handle coordinate picker hotkey"""
        print("\n" + "=" * 70)
        print(f"📍 Coordinate Picker Activated: {config.PICKER_HOTKEY_DISPLAY}")
        print("=" * 70)
        print("\n   Click anywhere on screen to capture coordinates")
        print("   Press ESC to cancel\n")

        # Activate picker in separate thread to avoid blocking
        def activate_picker():
            pick_coordinates(self.on_coordinates_picked)

        picker_thread = threading.Thread(target=activate_picker, daemon=True)
        picker_thread.start()

    def on_coordinates_picked(self, x: int, y: int):
        """Handle coordinates picked by user"""
        print(f"\n✅ Coordinates captured: ({x}, {y})")

        # Report to middleware
        # Note: We don't know which field is being picked without dashboard coordination
        # For now, just print. Full implementation in Phase 3.
        print(f"   Reported to middleware")
        self.middleware_client.report_picked_coordinates("unknown_field", x, y)

        print("=" * 70 + "\n")

    def on_visual_workflow_hotkey_pressed(self, hotkey: str):
        """Handle visual workflow execution hotkey"""
        print("\n" + "=" * 70)
        print(f"🎨 Visual Workflow Triggered: {hotkey}")
        print(f"   Timestamp: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print("=" * 70)

        try:
            # Get workflow ID
            workflow_id = self.visual_workflows.get(hotkey)
            if not workflow_id:
                print(f"   ❌ No workflow mapped to hotkey {hotkey}")
                print(f"   Available hotkeys: {list(self.visual_workflows.keys())}")
                return

            print(f"   Workflow: {workflow_id}")
            print("\n   🚀 Executing workflow...")

            # Execute visual workflow
            result = self.middleware_client.execute_visual_workflow(workflow_id)

            print(f"   📥 Received response from middleware")

            status = result.get('status')
            execution_time = result.get('execution_time_ms', 0)

            print(f"   ✅ Execution complete ({execution_time}ms)")
            print(f"   Status: {status}")

            if status == 'error':
                error_msg = result.get('error', 'Unknown error')
                print(f"\n   ❌ Error: {error_msg}")
                if result.get('step_id'):
                    print(f"   Failed at step: {result['step_id']}")
            elif status == 'success':
                variables = result.get('variables', {})
                if variables:
                    print(f"\n   📊 Results:")
                    for key, value in variables.items():
                        if isinstance(value, dict):
                            print(f"      {key}:")
                            for k, v in value.items():
                                print(f"         {k}: {v}")
                        else:
                            print(f"      {key}: {value}")

            print("=" * 70 + "\n")

        except MiddlewareError as e:
            print(f"\n   ❌ Middleware error: {e}")
            print(f"   Error code: {e.error_code}")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\n   ❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 70 + "\n")

    def on_hotkey_pressed(self, hotkey: str):
        """
        Callback when hotkey is pressed

        Args:
            hotkey: The hotkey that was pressed (normalized)
        """
        print("\n" + "=" * 70)
        print(f"🎹 Hotkey detected: {hotkey}")
        print("=" * 70)

        try:
            # 1. Capture context
            print("\n📸 Capturing context...")
            context = self.context_capturer.capture(
                hotkey=hotkey,
                user_id=config.USER_ID
            )

            # Check if DXCare is active
            if not self.context_capturer.is_dxcare_active(config.DXCARE_WINDOW_KEYWORDS):
                print("   ⚠️  Warning: DXCare window not detected")
                print(f"   Active window: {context.get('window_title', 'Unknown')}")

            # Show captured context
            selected_text = context.get('selected_text', '')
            if selected_text:
                preview = selected_text[:100] + "..." if len(selected_text) > 100 else selected_text
                print(f"   Selected text: {preview}")
            else:
                print("   ⚠️  No text selected")

            # 2. Call middleware
            print("\n📡 Calling middleware...")
            print(f"   Endpoint: {config.MIDDLEWARE_URL}/api/trigger")

            response = self.middleware_client.trigger_workflow(
                hotkey=hotkey,
                context=context
            )

            # 3. Check response
            status = response.get('status')
            workflow_id = response.get('workflow_id')
            execution_time = response.get('execution_time_ms', 0)

            print(f"   ✅ Response received ({execution_time}ms)")
            print(f"   Workflow: {workflow_id}")
            print(f"   Status: {status}")

            if status == 'error':
                error_msg = response.get('error_message', 'Unknown error')
                print(f"\n   ❌ Workflow error: {error_msg}")
                return

            # 4. Get insertion instructions
            insertions = response.get('insertions', [])

            if not insertions:
                print("\n   ⚠️  No insertion instructions received")
                return

            print(f"\n   📝 Received {len(insertions)} insertion(s)")

            # 5. Restore clipboard (so we don't pollute it)
            if config.BACKUP_CLIPBOARD:
                self.context_capturer.restore_clipboard()

            # 6. Perform insertions
            if config.AUTO_INSERT_ENABLED:
                self.inserter.insert_multiple(
                    insertions,
                    pause_before=config.INSERT_PAUSE_BEFORE,
                    pause_between=config.INSERT_PAUSE_AFTER
                )
            else:
                print("\n   ⚠️  Auto-insert disabled - showing instructions only:")
                for inst in insertions:
                    print(f"      {inst['target_field']} = {inst['content'][:50]}...")

            print("=" * 70 + "\n")

        except MiddlewareError as e:
            print(f"\n❌ Middleware error: {e}")
            print(f"   Error code: {e.error_code}")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 70 + "\n")


def main():
    """Main entry point"""
    agent = HackAppAgent()
    agent.start()


if __name__ == "__main__":
    main()
