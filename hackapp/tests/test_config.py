"""
Test Configuration Loading
Run this after installing dependencies: pip install -r middleware/requirements.txt
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from middleware.config_loader import load_all_configs


def test_config_loading():
    """Test that all configurations load correctly"""
    print("Testing configuration loader...")
    print("=" * 60)

    try:
        workflows, connectors, icd10 = load_all_configs("config")

        print("\n📋 Loaded Workflows:")
        for wf in workflows:
            status = "✅" if wf.enabled else "❌"
            print(f"  {status} {wf.workflow_id}: {wf.hotkey} -> {wf.connector}")

        print("\n🔌 Loaded Connectors:")
        for name, conn in connectors.items():
            print(f"  • {name}: {conn.base_url}")

        print(f"\n🏥 Loaded {len(icd10)} ICD-10 Codes")

        assert len(workflows) > 0, "No workflows loaded"
        assert len(connectors) > 0, "No connectors loaded"
        assert len(icd10) > 0, "No ICD-10 codes loaded"

        print("\n✅ All tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config_loading()
    sys.exit(0 if success else 1)
