"""
Field Inserter
UI automation for inserting data into DXCare fields
"""

import pyautogui
import time
from typing import List


class FieldInserter:
    """Handles automated data insertion into fields"""

    def __init__(self, insert_delay_ms: int = 10):
        """
        Initialize field inserter

        Args:
            insert_delay_ms: Delay between keystrokes in milliseconds
        """
        self.insert_delay = insert_delay_ms / 1000.0  # Convert to seconds

        # PyAutoGUI settings
        pyautogui.PAUSE = 0.05  # Small pause between pyautogui calls
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort

    def insert(self, instruction: dict, pause_before: float = 0.5, pause_after: float = 0.2):
        """
        Insert data into field based on instruction

        Args:
            instruction: Insertion instruction dictionary
            pause_before: Pause before insertion (seconds)
            pause_after: Pause after insertion (seconds)
        """
        target_field = instruction.get('target_field')
        content = instruction.get('content')
        mode = instruction.get('mode', 'replace')
        navigation = instruction.get('navigation')

        print(f"\n   📝 Inserting into {target_field}...")
        print(f"      Mode: {mode}")
        print(f"      Content: {content[:50]}..." if len(content) > 50 else f"      Content: {content}")

        # Pause before starting
        time.sleep(pause_before)

        # Handle mode
        if mode == "replace":
            self._replace_content(content)
        elif mode == "append":
            self._append_content(content)
        elif mode == "prepend":
            self._prepend_content(content)

        # Handle navigation to next field if specified
        if navigation:
            time.sleep(0.2)
            self._navigate(navigation)

        # Pause after insertion
        time.sleep(pause_after)

        print(f"      ✅ Inserted successfully")

    def _replace_content(self, content: str):
        """
        Replace current field content

        Args:
            content: New content
        """
        # Select all existing content
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)

        # Delete
        pyautogui.press('delete')
        time.sleep(0.05)

        # Type new content
        self._type_text(content)

    def _append_content(self, content: str):
        """
        Append to current field content

        Args:
            content: Content to append
        """
        # Move to end
        pyautogui.hotkey('ctrl', 'end')
        time.sleep(0.05)

        # Add space or newline before appending
        pyautogui.write('\n')
        time.sleep(0.05)

        # Type content
        self._type_text(content)

    def _prepend_content(self, content: str):
        """
        Prepend to current field content

        Args:
            content: Content to prepend
        """
        # Move to beginning
        pyautogui.hotkey('ctrl', 'home')
        time.sleep(0.05)

        # Type content
        self._type_text(content)

        # Add space or newline after prepending
        pyautogui.write('\n')

    def _type_text(self, text: str):
        """
        Type text with configured delay

        Args:
            text: Text to type
        """
        # Use pyautogui.write for faster typing
        # Note: interval is delay between characters
        pyautogui.write(text, interval=self.insert_delay)

    def _navigate(self, navigation_instruction: str):
        """
        Navigate to another field

        Args:
            navigation_instruction: Navigation command (e.g., "tab_3", "enter")
        """
        if navigation_instruction.startswith("tab_"):
            # Extract number of tabs
            try:
                count = int(navigation_instruction.split("_")[1])
                print(f"      ↹ Pressing Tab {count} times...")
                for _ in range(count):
                    pyautogui.press('tab')
                    time.sleep(0.1)
            except (IndexError, ValueError):
                print(f"      ⚠️  Invalid navigation instruction: {navigation_instruction}")

        elif navigation_instruction == "enter":
            pyautogui.press('enter')

        elif navigation_instruction.startswith("down_"):
            try:
                count = int(navigation_instruction.split("_")[1])
                for _ in range(count):
                    pyautogui.press('down')
                    time.sleep(0.1)
            except (IndexError, ValueError):
                print(f"      ⚠️  Invalid navigation instruction: {navigation_instruction}")

    def insert_multiple(
        self,
        instructions: List[dict],
        pause_before: float = 0.5,
        pause_between: float = 0.2
    ):
        """
        Insert multiple fields in sequence

        Args:
            instructions: List of insertion instructions
            pause_before: Pause before starting (seconds)
            pause_between: Pause between insertions (seconds)
        """
        print(f"\n📝 Inserting {len(instructions)} field(s)...")

        for i, instruction in enumerate(instructions):
            pause = pause_before if i == 0 else pause_between
            self.insert(instruction, pause_before=pause, pause_after=pause_between)

        print(f"✅ All {len(instructions)} field(s) inserted successfully!\n")


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing field inserter...")
    print("=" * 60)
    print("\n⚠️  This will start typing in 3 seconds!")
    print("   Open a text editor (Notepad) and click into it now!")
    print("\n   Countdown:")

    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    print("\n   Starting insertion test...\n")

    inserter = FieldInserter(insert_delay_ms=5)

    # Test 1: Replace mode
    test_instruction = {
        'target_field': 'TestField',
        'content': 'This is a test insertion from HackApp Agent!',
        'mode': 'replace',
        'navigation': None
    }

    inserter.insert(test_instruction)

    print("\n✅ Inserter test complete!")
    print("   Check your text editor - you should see the test text.")
