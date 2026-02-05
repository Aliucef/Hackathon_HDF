"""
HackApp Agent - Desktop Client
Main entry point for the agent application
"""

import sys
from hotkey_listener import HotkeyListener
from context_capture import ContextCapture
from inserter import FieldInserter
from middleware_client import MiddlewareClient, MiddlewareError
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

        self.hotkey_listener = HotkeyListener(
            hotkeys=config.HOTKEYS,
            callback=self.on_hotkey_pressed
        )

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

        # List available workflows
        workflows = self.middleware_client.list_workflows()
        if workflows:
            print(f"\n📋 Loaded {len(workflows)} workflow(s):")
            for wf in workflows:
                print(f"   • {wf['hotkey']}: {wf['name']}")

        # Start hotkey listener
        self.hotkey_listener.start()

        print("\n" + "=" * 70)
        print("✅ HackApp Agent is Ready!")
        print("=" * 70)
        print("\n💡 Usage:")
        print("   1. Open DXCare (or text editor for demo)")
        print("   2. Select clinical text")
        print("   3. Press a registered hotkey (e.g., CTRL+ALT+V)")
        print("   4. Watch fields auto-fill!")
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
        print("✅ Agent stopped\n")

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
