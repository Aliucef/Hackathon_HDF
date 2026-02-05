"""
Visual Workflow System
Drag-and-drop workflow builder for automation orchestration
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import json
from pathlib import Path


# ============================================================================
# Step Models
# ============================================================================

class WorkflowStep(BaseModel):
    """Base class for workflow steps"""
    step_id: str = Field(..., description="Unique step identifier")
    step_type: Literal["read_coords", "lookup_excel", "lookup_db", "lookup_api", "write_coords", "speech_to_text"]
    name: str = Field(..., description="Human-readable step name")
    enabled: bool = True


class ReadCoordsStep(WorkflowStep):
    """Read text from screen coordinates"""
    step_type: Literal["read_coords"] = "read_coords"
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    width: int = Field(200, description="Width of capture area")
    height: int = Field(30, description="Height of capture area")
    output_variable: str = Field("text", description="Variable name to store result")


class LookupExcelStep(WorkflowStep):
    """Lookup data in Excel file"""
    step_type: Literal["lookup_excel"] = "lookup_excel"
    file_path: str = Field(..., description="Path to Excel file")
    sheet_name: str = Field("Sheet1", description="Sheet name")
    search_column: str = Field(..., description="Column to search (e.g., 'A' or 'Patient Name')")
    search_value_variable: str = Field(..., description="Variable containing value to search for")
    return_columns: List[str] = Field(..., description="Columns to return (e.g., ['B', 'C'] or ['Age', 'Diagnosis'])")
    output_variable: str = Field("excel_data", description="Variable name to store results")


class LookupDbStep(WorkflowStep):
    """Lookup data in database"""
    step_type: Literal["lookup_db"] = "lookup_db"
    connection_string: str = Field(..., description="Database connection string")
    query: str = Field(..., description="SQL query with {variable} placeholders")
    output_variable: str = Field("db_data", description="Variable name to store results")


class LookupApiStep(WorkflowStep):
    """Call external API"""
    step_type: Literal["lookup_api"] = "lookup_api"
    url: str = Field(..., description="API endpoint URL")
    method: Literal["GET", "POST", "PUT"] = "POST"
    headers: Dict[str, str] = Field(default_factory=dict)
    body_template: str = Field(..., description="Request body template with {variable} placeholders")
    output_variable: str = Field("api_data", description="Variable name to store response")


class WriteCoordsStep(WorkflowStep):
    """Write text to screen coordinates"""
    step_type: Literal["write_coords"] = "write_coords"
    x: int = Field(..., description="X coordinate to click")
    y: int = Field(..., description="Y coordinate to click")
    content_template: str = Field(..., description="Content template with {variable} placeholders")
    insert_method: Literal["type", "paste"] = "paste"


class SpeechToTextStep(WorkflowStep):
    """Speech-to-text capture"""
    step_type: Literal["speech_to_text"] = "speech_to_text"
    language: str = Field("en-US", description="Language code")
    output_variable: str = Field("speech_text", description="Variable name to store transcription")


# ============================================================================
# Visual Workflow Model
# ============================================================================

class VisualWorkflow(BaseModel):
    """Complete visual workflow definition"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = None
    hotkey: Optional[str] = Field(None, description="Execution hotkey binding (e.g., CTRL+ALT+E)")
    enabled: bool = True
    steps: List[Dict[str, Any]] = Field(..., description="Ordered list of steps")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "excel_patient_lookup",
                "name": "Excel Patient Lookup",
                "description": "Read patient name, lookup in Excel, write results",
                "hotkey": "CTRL+ALT+P",
                "steps": [
                    {
                        "step_id": "1",
                        "step_type": "read_coords",
                        "name": "Get patient name",
                        "x": 100,
                        "y": 200,
                        "output_variable": "patient_name"
                    },
                    {
                        "step_id": "2",
                        "step_type": "lookup_excel",
                        "name": "Lookup patient data",
                        "file_path": "patients.xlsx",
                        "search_column": "Patient Name",
                        "search_value_variable": "patient_name",
                        "return_columns": ["Age", "Diagnosis"],
                        "output_variable": "patient_data"
                    },
                    {
                        "step_id": "3",
                        "step_type": "write_coords",
                        "name": "Write results",
                        "x": 400,
                        "y": 350,
                        "content_template": "Age: {patient_data.Age}, Diagnosis: {patient_data.Diagnosis}",
                        "insert_method": "paste"
                    }
                ]
            }
        }


# ============================================================================
# Storage
# ============================================================================

class VisualWorkflowStorage:
    """Persist visual workflows to JSON file"""

    def __init__(self, storage_path: str = "config/visual_workflows.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._save_all([])

    def _save_all(self, workflows: List[VisualWorkflow]):
        """Save all workflows to file"""
        data = [wf.model_dump(mode='json') for wf in workflows]
        self.storage_path.write_text(json.dumps(data, indent=2, default=str))

    def _load_all(self) -> List[VisualWorkflow]:
        """Load all workflows from file"""
        if not self.storage_path.exists():
            return []
        data = json.loads(self.storage_path.read_text())
        return [VisualWorkflow(**wf) for wf in data]

    def list(self) -> List[VisualWorkflow]:
        """Get all workflows"""
        return self._load_all()

    def get(self, workflow_id: str) -> Optional[VisualWorkflow]:
        """Get workflow by ID"""
        workflows = self._load_all()
        for wf in workflows:
            if wf.workflow_id == workflow_id:
                return wf
        return None

    def create(self, workflow: VisualWorkflow) -> VisualWorkflow:
        """Create new workflow"""
        workflows = self._load_all()

        # Check for duplicate ID
        if any(wf.workflow_id == workflow.workflow_id for wf in workflows):
            raise ValueError(f"Workflow ID '{workflow.workflow_id}' already exists")

        workflows.append(workflow)
        self._save_all(workflows)
        return workflow

    def update(self, workflow_id: str, workflow: VisualWorkflow) -> VisualWorkflow:
        """Update existing workflow"""
        workflows = self._load_all()

        for i, wf in enumerate(workflows):
            if wf.workflow_id == workflow_id:
                workflow.updated_at = datetime.now()
                workflows[i] = workflow
                self._save_all(workflows)
                return workflow

        raise ValueError(f"Workflow '{workflow_id}' not found")

    def delete(self, workflow_id: str):
        """Delete workflow"""
        workflows = self._load_all()
        workflows = [wf for wf in workflows if wf.workflow_id != workflow_id]
        self._save_all(workflows)
