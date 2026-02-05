"""
HackApp Data Models
Pydantic models for all data structures used across the system
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal, Any
from datetime import datetime
import re


# ============================================================================
# CONTEXT MODELS (Input from Agent)
# ============================================================================

class Context(BaseModel):
    """Context captured by the agent when hotkey is triggered"""
    hotkey: str = Field(..., description="The hotkey combination pressed")
    active_field: Optional[str] = Field(None, description="Currently active field name")
    selected_text: Optional[str] = Field(None, description="Text selected by user")
    clipboard_text: Optional[str] = Field(None, description="Current clipboard content")
    window_title: Optional[str] = Field(None, description="Active window title")
    user_id: Optional[str] = Field(None, description="User identifier (if available)")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "hotkey": "CTRL+ALT+V",
                "selected_text": "Patient presents with cough and fever",
                "window_title": "DXCare - Patient Chart",
                "user_id": "clinician_123"
            }
        }


# ============================================================================
# WORKFLOW CONFIGURATION MODELS
# ============================================================================

class InputConfig(BaseModel):
    """Configuration for workflow input"""
    source: Literal["selected_text", "clipboard", "active_field_text"] = "selected_text"
    validation: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "source": "selected_text",
                "validation": {
                    "min_length": 10,
                    "max_length": 5000
                }
            }
        }


class RequestConfig(BaseModel):
    """Configuration for external API request"""
    template: str = Field(..., description="Jinja2 template for request body")
    timeout: int = Field(30, description="Request timeout in seconds", ge=1, le=300)
    method: Literal["POST", "GET", "PUT"] = "POST"

    class Config:
        json_schema_extra = {
            "example": {
                "template": "Summarize: {{ input_text }}",
                "timeout": 30,
                "method": "POST"
            }
        }


class ResponseMapping(BaseModel):
    """Mapping configuration for extracting data from API response"""
    mappings: Dict[str, str] = Field(..., description="JSONPath mappings for response fields")

    class Config:
        json_schema_extra = {
            "example": {
                "mappings": {
                    "summary": "$.summary",
                    "icd10_code": "$.icd10.code",
                    "icd10_label": "$.icd10.label"
                }
            }
        }


class OutputConfig(BaseModel):
    """Configuration for a single output field insertion"""
    type: Literal["text", "icd10"] = "text"
    target_field: str = Field(..., description="Target DXCare field name")
    content: str = Field(..., description="Jinja2 template for content")
    mode: Literal["replace", "append", "prepend"] = "replace"
    navigation: Optional[str] = Field(None, description="Navigation instruction (e.g., 'tab_3')")
    label: Optional[str] = Field(None, description="Optional label for ICD-10 codes")
    click_before: Optional[str] = Field(None, description="Screen coordinates to click before inserting (format: 'x,y')")
    insert_method: Literal["type", "paste"] = Field("type", description="type = character by character; paste = clipboard paste")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "target_field": "DiagnosisText",
                "content": "{{ summary }}",
                "mode": "replace"
            }
        }


class SecurityConfig(BaseModel):
    """Security configuration for workflow"""
    allowed_fields: List[str] = Field(default_factory=list, description="Whitelist of allowed target fields")
    require_confirmation: bool = Field(False, description="Require user confirmation before insertion")
    max_response_size: int = Field(100000, description="Maximum response size in bytes")

    class Config:
        json_schema_extra = {
            "example": {
                "allowed_fields": ["DiagnosisText", "DiagnosisCode", "ClinicalNotes"],
                "require_confirmation": False
            }
        }


class ValidationConfig(BaseModel):
    """Validation configuration for workflow responses"""
    required_fields: List[str] = Field(default_factory=list, description="Required fields in response")
    icd10_format: bool = Field(False, description="Validate ICD-10 code format")


class WorkflowConfig(BaseModel):
    """Complete workflow configuration"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Human-readable workflow name")
    hotkey: str = Field(..., description="Hotkey combination that triggers this workflow")
    enabled: bool = Field(True, description="Whether workflow is active")

    input: InputConfig
    connector: str = Field(..., description="Connector name to use")
    request: RequestConfig
    response: ResponseMapping
    validation: Optional[ValidationConfig] = None
    output: List[OutputConfig]
    security: Optional[SecurityConfig] = Field(default_factory=SecurityConfig)

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "voice_summary_icd10",
                "name": "Voice AI Clinical Summary with ICD-10",
                "hotkey": "CTRL+ALT+V",
                "enabled": True,
                "connector": "voice_ai",
                "input": {"source": "selected_text"},
                "request": {"template": "Summarize: {{ input_text }}"},
                "response": {"mappings": {"summary": "$.summary"}},
                "output": [{"type": "text", "target_field": "DiagnosisText", "content": "{{ summary }}"}]
            }
        }


# ============================================================================
# CONNECTOR CONFIGURATION MODELS
# ============================================================================

class AuthConfig(BaseModel):
    """Authentication configuration for external services"""
    type: Literal["bearer_token", "api_key", "basic", "none"] = "none"
    token_env: Optional[str] = Field(None, description="Environment variable name for token")
    token: Optional[str] = Field(None, description="Hardcoded token (not recommended for production)")
    header: Optional[str] = Field(None, description="Header name for api_key auth")
    username: Optional[str] = None
    password: Optional[str] = None


class RetryPolicy(BaseModel):
    """Retry policy for external API calls"""
    max_retries: int = Field(2, ge=0, le=5)
    backoff: Literal["fixed", "exponential"] = "exponential"
    initial_delay: float = Field(1.0, gt=0)


class ConnectorConfig(BaseModel):
    """Configuration for external service connector"""
    type: Literal["rest_api", "soap", "custom"] = "rest_api"
    base_url: str = Field(..., description="Base URL for the external service")
    auth: Optional[AuthConfig] = Field(default_factory=AuthConfig)
    endpoints: Dict[str, str] = Field(..., description="Named endpoints")
    timeout: int = Field(30, ge=1, le=300)
    retry_policy: Optional[RetryPolicy] = Field(default_factory=RetryPolicy)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "type": "rest_api",
                "base_url": "http://localhost:5001",
                "endpoints": {"summarize": "/api/clinical_summary"},
                "timeout": 30
            }
        }


# ============================================================================
# INSERTION INSTRUCTION MODELS (Output to Agent)
# ============================================================================

class InsertionInstruction(BaseModel):
    """Single field insertion instruction for the agent"""
    target_field: str = Field(..., description="Target field name")
    content: str = Field(..., description="Content to insert")
    mode: Literal["replace", "append", "prepend"] = "replace"
    type: Literal["text", "icd10"] = "text"
    navigation: Optional[str] = Field(None, description="Navigation instruction")
    label: Optional[str] = Field(None, description="Display label for ICD-10")
    click_before: Optional[str] = Field(None, description="Screen coordinates to click before inserting (format: 'x,y')")
    insert_method: Literal["type", "paste"] = Field("type", description="type = character by character; paste = clipboard paste")

    class Config:
        json_schema_extra = {
            "example": {
                "target_field": "DiagnosisText",
                "content": "Pneumonia with respiratory symptoms",
                "mode": "replace",
                "type": "text"
            }
        }


class WorkflowResponse(BaseModel):
    """Complete response from middleware to agent"""
    status: Literal["success", "error"]
    workflow_id: str
    insertions: List[InsertionInstruction] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_ms: int = Field(..., ge=0)
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "workflow_id": "voice_summary_icd10",
                "insertions": [
                    {
                        "target_field": "DiagnosisText",
                        "content": "Pneumonia",
                        "mode": "replace"
                    }
                ],
                "execution_time_ms": 1234
            }
        }


# ============================================================================
# ICD-10 MODELS
# ============================================================================

class ICD10Code(BaseModel):
    """ICD-10 diagnosis code"""
    code: str = Field(..., description="ICD-10 code", pattern=r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')
    label: Optional[str] = Field(None, description="Human-readable label")
    category: Optional[str] = Field(None, description="Disease category")

    @validator('code')
    def validate_icd10_format(cls, v):
        """Validate ICD-10 code format"""
        pattern = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')
        if not pattern.match(v):
            raise ValueError(f"Invalid ICD-10 code format: {v}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "code": "J18.9",
                "label": "Pneumonia, unspecified organism",
                "category": "Respiratory"
            }
        }


# ============================================================================
# VALIDATION RESULT MODELS
# ============================================================================

class ValidationResult(BaseModel):
    """Result of a validation operation"""
    valid: bool
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# AUDIT LOG MODELS (PHI-Free)
# ============================================================================

class AuditLogEntry(BaseModel):
    """Audit log entry - NO CLINICAL DATA"""
    timestamp: datetime = Field(default_factory=datetime.now)
    workflow_id: str
    user_id: Optional[str] = None
    connector: str
    status: Literal["success", "error", "timeout"]
    execution_time_ms: int
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-05T10:30:00Z",
                "workflow_id": "voice_summary_icd10",
                "user_id": "clinician_123",
                "connector": "voice_ai",
                "status": "success",
                "execution_time_ms": 1234
            }
        }


# ============================================================================
# API REQUEST/RESPONSE MODELS
# ============================================================================

class TriggerRequest(BaseModel):
    """Request to trigger a workflow"""
    hotkey: str
    context: Context


class HealthResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    workflows_loaded: int
    connectors_active: int
    version: str = "1.0.0"
    uptime_seconds: Optional[float] = None


class WorkflowListResponse(BaseModel):
    """List of available workflows"""
    workflows: List[Dict[str, Any]]
    total: int
