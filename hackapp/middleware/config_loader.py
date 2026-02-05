"""
Configuration Loader
Loads and validates YAML configuration files
"""

import yaml
from pathlib import Path
from typing import List, Dict
from pydantic import ValidationError

from middleware.models import WorkflowConfig, ConnectorConfig, ICD10Code


class ConfigLoader:
    """Loads and validates configuration files"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        if not self.config_dir.exists():
            # Try relative to middleware directory
            self.config_dir = Path(__file__).parent.parent / "config"

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

    def load_workflows(self) -> List[WorkflowConfig]:
        """Load and validate workflow configurations"""
        workflow_file = self.config_dir / "workflows.yaml"

        if not workflow_file.exists():
            raise FileNotFoundError(f"Workflows config not found: {workflow_file}")

        with open(workflow_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        workflows = []
        errors = []

        for workflow_data in data.get('workflows', []):
            try:
                workflow = WorkflowConfig(**workflow_data)
                workflows.append(workflow)
            except ValidationError as e:
                errors.append({
                    'workflow_id': workflow_data.get('workflow_id', 'unknown'),
                    'errors': e.errors()
                })

        if errors:
            error_msg = "Workflow validation errors:\n"
            for err in errors:
                error_msg += f"  {err['workflow_id']}: {err['errors']}\n"
            raise ValueError(error_msg)

        print(f"✅ Loaded {len(workflows)} workflows")
        return workflows

    def load_connectors(self) -> Dict[str, ConnectorConfig]:
        """Load and validate connector configurations"""
        connector_file = self.config_dir / "connectors.yaml"

        if not connector_file.exists():
            raise FileNotFoundError(f"Connectors config not found: {connector_file}")

        with open(connector_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        connectors = {}
        errors = []

        for name, connector_data in data.get('connectors', {}).items():
            try:
                connector = ConnectorConfig(**connector_data)
                connectors[name] = connector
            except ValidationError as e:
                errors.append({
                    'connector': name,
                    'errors': e.errors()
                })

        if errors:
            error_msg = "Connector validation errors:\n"
            for err in errors:
                error_msg += f"  {err['connector']}: {err['errors']}\n"
            raise ValueError(error_msg)

        print(f"✅ Loaded {len(connectors)} connectors")
        return connectors

    def load_icd10_catalog(self) -> Dict[str, ICD10Code]:
        """Load ICD-10 mini catalog"""
        icd10_file = self.config_dir / "icd10_mini.yaml"

        if not icd10_file.exists():
            print(f"⚠️  ICD-10 catalog not found: {icd10_file}, using empty catalog")
            return {}

        with open(icd10_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        catalog = {}
        errors = []

        for code, code_data in data.get('icd10_codes', {}).items():
            try:
                icd10_code = ICD10Code(**code_data)
                catalog[code] = icd10_code
            except ValidationError as e:
                errors.append({
                    'code': code,
                    'errors': e.errors()
                })

        if errors:
            print(f"⚠️  ICD-10 validation errors (skipped {len(errors)} codes):")
            for err in errors[:5]:  # Show first 5 errors
                print(f"    {err['code']}: {err['errors']}")

        print(f"✅ Loaded {len(catalog)} ICD-10 codes")
        return catalog


def load_all_configs(config_dir: str = "config") -> tuple:
    """
    Load all configurations at once

    Returns:
        tuple: (workflows, connectors, icd10_catalog)
    """
    loader = ConfigLoader(config_dir)

    workflows = loader.load_workflows()
    connectors = loader.load_connectors()
    icd10_catalog = loader.load_icd10_catalog()

    return workflows, connectors, icd10_catalog


# ============================================================================
# Test function
# ============================================================================

if __name__ == "__main__":
    """Test configuration loading"""
    print("Testing configuration loader...")
    print("=" * 60)

    try:
        workflows, connectors, icd10 = load_all_configs()

        print("\n📋 Loaded Workflows:")
        for wf in workflows:
            status = "✅" if wf.enabled else "❌"
            print(f"  {status} {wf.workflow_id}: {wf.hotkey} -> {wf.connector}")

        print("\n🔌 Loaded Connectors:")
        for name, conn in connectors.items():
            print(f"  • {name}: {conn.base_url}")

        print(f"\n🏥 Loaded {len(icd10)} ICD-10 Codes")
        print("  Sample codes:")
        for code in list(icd10.keys())[:5]:
            print(f"    {code}: {icd10[code].label}")

        print("\n✅ All configurations loaded successfully!")

    except Exception as e:
        print(f"\n❌ Error loading configurations: {e}")
        import traceback
        traceback.print_exc()
