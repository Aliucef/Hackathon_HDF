# HackApp Architecture Documentation
## Configurable Middleware for DXCare Integration

**Version**: 1.0
**Date**: 2026-02-05
**Status**: Hackathon Prototype

---

## Executive Summary

HackApp is a **non-intrusive middleware system** that extends DXCare functionality without modifying DXCare itself. It provides a configuration-driven framework for automating clinical workflows through external digital services.

**Core Value Proposition**: Enable clinicians to trigger AI-powered workflows (voice summarization, ICD-10 suggestion, decision support) via hotkeys while working in DXCare, with automatic data insertion back into DXCare fields.

---

## System Architecture

### Three-Layer Design (Strict Separation of Concerns)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT AGENT                              │
│  (Desktop Application - "The Hands")                             │
│                                                                   │
│  • Global hotkey listener (works when DXCare is active)          │
│  • Context capture (active field, selected text)                 │
│  • UI automation for data insertion                              │
│  • No business logic                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS + Token Auth
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MIDDLEWARE (HackApp Core)                    │
│  (REST API Server - "The Brain")                                 │
│                                                                   │
│  • Workflow engine (config-driven)                               │
│  • Connector abstraction layer                                   │
│  • Request/response transformation                               │
│  • Validation & security enforcement                             │
│  • Audit logging                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API Calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL CONNECTOR LAYER                       │
│  (Pluggable Integrations - "The Services")                       │
│                                                                   │
│  • Voice AI Service (clinical summarization)                     │
│  • Decision Support APIs                                         │
│  • Drug interaction checkers                                     │
│  • Custom business logic services                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Client Agent (Desktop Side)

### Responsibilities
- **Global Hotkey Listening**: Intercepts keyboard shortcuts system-wide (even when DXCare is the active application)
- **Context Capture**: Detects current state:
  - Active window title (verify DXCare is active)
  - Active field identifier (simulated for prototype)
  - Selected text or field content
- **Middleware Communication**: Sends context payload via REST API
- **Data Insertion**: Receives insertion instructions and executes via UI automation

### Technical Implementation

#### Hotkey Listening
- **Library**: `pynput` (cross-platform) or `keyboard` (Windows)
- **Mechanism**: Global keyboard hooks that work regardless of active application
- **Example**: `CTRL+ALT+V` triggers workflow even when DXCare window is focused

#### Context Capture Strategy
**Challenge**: We don't have DXCare API access or internal knowledge.

**Solutions** (ordered by hackathon feasibility):

1. **Clipboard-based** (Simplest):
   - User selects text in DXCare field
   - Presses hotkey
   - Agent reads from clipboard
   - No field name detection needed

2. **Window Title + Field Simulation** (Recommended):
   - Detect active window title contains "DXCare" or "Epic" (if using Epic DXCare)
   - Use predefined field mapping based on hotkey
   - Example: `CTRL+ALT+D` = "DiagnosisText field"

3. **OCR-based** (Advanced, probably overkill):
   - Screenshot active window
   - OCR to identify field labels
   - Not recommended for hackathon timeline

#### Data Insertion Methods

**Option A: UI Automation (Recommended for Hackathon)**
- **Libraries**:
  - Windows: `pyautogui`, `pywinauto`
  - Linux: `python-uinput`, `xdotool`
  - macOS: `pyautogui`
- **Mechanism**: Simulate keyboard input into active field
- **Process**:
  1. Verify DXCare window is active
  2. Focus target field (via Tab navigation or click coordinates)
  3. Clear existing content (Ctrl+A, Delete)
  4. Type new content character-by-character
  5. For ICD-10 codes: handle structured field input (Tab, Enter sequences)

**Option B: Clipboard Injection**
- Copy data to clipboard
- Simulate `Ctrl+V`
- Less reliable, doesn't handle multi-field insertion

**Option C: DXCare API (Ideal but unavailable)**
- Would require official DXCare integration credentials
- Not feasible for hackathon without vendor partnership

### Agent Constraints (CRITICAL)
- **No business logic**: Agent is a "dumb executor"
- **No external API calls**: Only communicates with middleware
- **No workflow definitions**: Doesn't know what workflows exist
- **Minimal permissions**: Only keyboard/mouse automation

### Data Flow (Agent Perspective)
```python
# Pseudocode
def on_hotkey_pressed(hotkey):
    context = capture_context()  # Field name, selected text, window title

    response = middleware.trigger_workflow(
        hotkey=hotkey,
        context=context
    )

    for instruction in response.insertions:
        insert_into_field(
            field=instruction.target_field,
            content=instruction.content,
            mode=instruction.mode  # replace, append, prepend
        )
```

---

## Layer 2: Middleware (HackApp Core)

### Responsibilities
- **Workflow Orchestration**: Match hotkeys to workflows, execute steps
- **Configuration Management**: Load and validate YAML/JSON configs
- **Connector Execution**: Call external services via abstraction layer
- **Data Transformation**: Apply templates, extract response fields
- **Validation**: Enforce security rules, validate ICD-10 codes, check field whitelists
- **Audit Logging**: Record workflow executions (no clinical text)

### Core Components

#### 2.1 Workflow Engine
Loads workflows from `config/workflows.yaml` and executes matching workflow on trigger.

**Workflow Definition Schema**:
```yaml
workflow_id: voice_summary_icd10
name: "Voice AI Clinical Summary with ICD-10"
hotkey: CTRL+ALT+V
enabled: true

input:
  source: selected_text  # or active_field_text, clipboard
  validation:
    min_length: 10
    max_length: 5000

connector: voice_ai  # References connector in connectors.yaml

request:
  template: |
    Analyze this clinical note and provide:
    1. A concise summary (2-3 sentences)
    2. Suggested primary ICD-10 diagnosis code

    Clinical Note:
    {{ input_text }}

  timeout: 30  # seconds

response:
  mappings:
    summary: $.summary        # JSONPath extraction
    icd10_code: $.icd10.code
    icd10_label: $.icd10.label

validation:
  required_fields: [summary, icd10_code]
  icd10_format: true  # Trigger ICD-10 regex validation

output:
  - type: text
    target_field: DiagnosisText
    content: "{{ summary }}"
    mode: replace

  - type: icd10
    target_field: DiagnosisCode
    content: "{{ icd10_code }}"
    label: "{{ icd10_label }}"
    mode: replace

security:
  allowed_fields: [DiagnosisText, DiagnosisCode, ChiefComplaint]
  require_confirmation: false  # For MVP
```

#### 2.2 Connector Abstraction
Each external service is a pluggable connector.

**Connector Config Schema** (`config/connectors.yaml`):
```yaml
connectors:
  voice_ai:
    type: rest_api
    base_url: http://localhost:5001/api
    auth:
      type: bearer_token
      token_env: VOICE_AI_TOKEN  # or hardcoded for MVP
    endpoints:
      summarize: /clinical_summary
    timeout: 30
    retry_policy:
      max_retries: 2
      backoff: exponential

  decision_support:
    type: rest_api
    base_url: https://api.example.com
    auth:
      type: api_key
      header: X-API-Key
      token_env: DECISION_SUPPORT_KEY
```

**Connector Interface** (Python):
```python
class Connector(ABC):
    @abstractmethod
    def execute(self, request: dict) -> dict:
        """Send request to external service, return normalized response"""
        pass

class RestApiConnector(Connector):
    def execute(self, request: dict) -> dict:
        # Handle HTTP call, error handling, retries
        response = requests.post(self.endpoint, json=request, timeout=self.timeout)
        return self.normalize_response(response.json())
```

#### 2.3 Transformation Layer
Uses **Jinja2** for template rendering:
- Request templates: inject context into API calls
- Response extraction: JSONPath or dict navigation
- Output formatting: prepare insertion instructions

#### 2.4 Validation Layer
**Security Validations**:
- Field whitelist: only allowed fields can be targeted
- Content length limits
- No script injection (basic XSS prevention)

**Medical Validations**:
- ICD-10 format: `^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$`
- ICD-10 code existence (optional mini-catalog lookup)

**Example Validator**:
```python
class ICD10Validator:
    PATTERN = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')

    def validate(self, code: str) -> ValidationResult:
        if not self.PATTERN.match(code):
            return ValidationResult(valid=False, error="Invalid ICD-10 format")
        return ValidationResult(valid=True)
```

#### 2.5 Audit Logger
**Log Only**:
- Timestamp
- Workflow ID
- User ID (if available)
- Connector called
- Success/failure status

**Never Log**:
- Clinical text content
- Patient identifiers
- API request/response bodies (in production)

#### 2.6 API Endpoints

**POST /api/trigger**
```json
Request:
{
  "hotkey": "CTRL+ALT+V",
  "context": {
    "active_field": "DiagnosisText",
    "selected_text": "Patient presents with...",
    "window_title": "DXCare - Patient Chart",
    "user_id": "clinician_123"
  }
}

Response:
{
  "status": "success",
  "workflow_id": "voice_summary_icd10",
  "insertions": [
    {
      "target_field": "DiagnosisText",
      "content": "Pneumonia, likely bacterial origin",
      "mode": "replace"
    },
    {
      "target_field": "DiagnosisCode",
      "content": "J18.9",
      "label": "Pneumonia, unspecified organism",
      "type": "icd10",
      "mode": "replace"
    }
  ],
  "execution_time_ms": 1234
}
```

**GET /api/health**
```json
{
  "status": "healthy",
  "workflows_loaded": 3,
  "connectors_active": 2
}
```

---

## Layer 3: External Connector Layer

### Mock External Service (For Hackathon)

**Endpoint**: `POST /api/clinical_summary`

**Request**:
```json
{
  "text": "Patient presents with persistent cough, fever 102F, chest pain. CXR shows infiltrates."
}
```

**Response**:
```json
{
  "summary": "Pneumonia with respiratory symptoms and radiological findings",
  "icd10": {
    "code": "J18.9",
    "label": "Pneumonia, unspecified organism"
  },
  "confidence": 0.87,
  "processing_time_ms": 234
}
```

**Implementation**: Simple Flask app with hardcoded logic:
- Keyword matching (e.g., "cough" + "infiltrates" → pneumonia)
- Small lookup table of common diagnoses
- No real AI for MVP

---

## Data Models (Pydantic)

### Core Models

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class Context(BaseModel):
    """Context captured by agent"""
    hotkey: str
    active_field: Optional[str] = None
    selected_text: Optional[str] = None
    window_title: Optional[str] = None
    user_id: Optional[str] = None

class InsertionInstruction(BaseModel):
    """Single field insertion instruction"""
    target_field: str
    content: str
    mode: Literal["replace", "append", "prepend"] = "replace"
    type: Literal["text", "icd10"] = "text"
    label: Optional[str] = None  # For ICD-10 display

class WorkflowResponse(BaseModel):
    """Response from middleware to agent"""
    status: Literal["success", "error"]
    workflow_id: str
    insertions: List[InsertionInstruction]
    error_message: Optional[str] = None
    execution_time_ms: int

class WorkflowConfig(BaseModel):
    """Workflow definition from YAML"""
    workflow_id: str
    name: str
    hotkey: str
    enabled: bool = True
    input: Dict
    connector: str
    request: Dict
    response: Dict
    output: List[Dict]
    security: Optional[Dict] = None

class ICD10Code(BaseModel):
    """ICD-10 diagnosis code"""
    code: str = Field(pattern=r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')
    label: Optional[str] = None
```

---

## Security Model (Hackathon-Appropriate)

### Authentication
- **Agent ↔ Middleware**: Bearer token (hardcoded in config for MVP)
- **Middleware ↔ External Services**: Service-specific (API keys, tokens)

### Authorization
- **Field Whitelist**: Only pre-approved fields can be written to
- **Workflow Whitelist**: Only enabled workflows can execute

### Data Protection
- **No PHI in Logs**: Audit logs contain only metadata
- **Content Validation**: Length limits, type checking
- **Secure Config Storage**: `.env` file for secrets (gitignored)

### Not Implemented (Out of Scope for Hackathon)
- HTTPS enforcement (localhost OK)
- User authentication (assume single clinician)
- Role-based access control
- Encrypted storage
- HIPAA compliance audit trail

---

## Execution Flow (End-to-End)

### Happy Path: Voice Summary with ICD-10

```
1. [DXCare] Clinician selects clinical note text
2. [DXCare] Clinician presses CTRL+ALT+V
3. [Agent] Hotkey listener detects trigger
4. [Agent] Captures context:
   - hotkey: "CTRL+ALT+V"
   - selected_text: "Patient presents with..."
   - window_title: "DXCare - Patient Chart"
5. [Agent] HTTP POST to middleware:
   POST http://localhost:5000/api/trigger
6. [Middleware] Workflow engine:
   - Matches hotkey → "voice_summary_icd10" workflow
   - Validates input (length, required fields)
   - Loads connector config for "voice_ai"
7. [Middleware] Transformer:
   - Renders request template with input text
   - Prepares API call payload
8. [Middleware] Connector:
   - Calls external service: POST http://localhost:5001/api/clinical_summary
   - Receives response with summary + ICD-10 code
9. [Middleware] Validator:
   - Validates ICD-10 code format (J18.9)
   - Checks field whitelist (DiagnosisText, DiagnosisCode allowed)
10. [Middleware] Transformer:
    - Extracts summary and ICD-10 from response
    - Builds insertion instructions
11. [Middleware] Audit Logger:
    - Logs: timestamp, workflow_id, success, duration
12. [Middleware] Returns response to agent
13. [Agent] Executes insertions:
    - Focus DiagnosisText field (via Tab or click)
    - Types: "Pneumonia with respiratory symptoms..."
    - Focus DiagnosisCode field
    - Types: "J18.9" + Enter
14. [DXCare] Fields now populated with AI-generated content
15. [Clinician] Reviews and confirms/edits as needed
```

### Error Handling

**Scenario: Invalid ICD-10 Code**
```
9. [Middleware] Validator detects invalid code: "XYZ123"
10. [Middleware] Returns error response:
    {
      "status": "error",
      "workflow_id": "voice_summary_icd10",
      "error_message": "Invalid ICD-10 format: XYZ123",
      "insertions": []
    }
11. [Agent] Displays error notification to user
12. [Clinician] Manually enters diagnosis
```

---

## Technology Stack

### Client Agent
- **Language**: Python 3.9+
- **Hotkey Listening**: `pynput` or `keyboard`
- **UI Automation**: `pyautogui`, `pywinauto` (Windows)
- **HTTP Client**: `requests`

### Middleware
- **Framework**: Flask or FastAPI (recommend FastAPI for auto docs)
- **Config Parsing**: PyYAML
- **Data Validation**: Pydantic
- **Template Engine**: Jinja2
- **HTTP Client**: `requests` or `httpx`

### Mock External Service
- **Framework**: Flask (minimal)
- **Data**: Hardcoded lookup dictionaries

### Development Tools
- **Testing**: pytest
- **Linting**: ruff or pylint
- **Type Checking**: mypy (optional)

---

## Configuration-Driven Design

### Zero-Code Principle
New workflows are added by **editing YAML files only**, no code changes required.

### Example: Adding a New Workflow

**Scenario**: Add drug interaction checker

**Step 1**: Add connector (`config/connectors.yaml`):
```yaml
drug_interaction:
  type: rest_api
  base_url: http://localhost:5002/api
  endpoints:
    check: /drug_interaction
```

**Step 2**: Add workflow (`config/workflows.yaml`):
```yaml
- workflow_id: drug_interaction_check
  name: "Check Drug Interactions"
  hotkey: CTRL+ALT+D
  input:
    source: selected_text
  connector: drug_interaction
  request:
    template: |
      Check interactions for: {{ input_text }}
  response:
    mappings:
      interactions: $.interactions
      severity: $.severity
  output:
    - type: text
      target_field: ClinicalNotes
      content: "Drug Interactions ({{ severity }}): {{ interactions }}"
      mode: append
```

**Step 3**: Restart middleware (no code changes needed)

---

## ICD-10 Support (Deep Dive)

### Why ICD-10 Matters
- **Billing**: Required for insurance claims
- **Interoperability**: Standardized across EMRs
- **Analytics**: Population health, quality metrics
- **Regulatory**: HIPAA, Meaningful Use requirements

### HackApp's ICD-10 Strategy

#### Minimal Validation (Hackathon Scope)
- **Format Validation Only**: Regex pattern matching
- **No Semantic Validation**: Don't verify code exists in official catalog
- **No Version Checking**: Assume ICD-10-CM current year

#### ICD-10 Data Structure
```python
class ICD10Code(BaseModel):
    code: str  # e.g., "J18.9"
    label: Optional[str]  # e.g., "Pneumonia, unspecified organism"
    category: Optional[str]  # e.g., "Diseases of the respiratory system"
```

#### Validation Rules
1. **Format**: Must match `[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?`
2. **Length**: 3-7 characters
3. **Structure**:
   - Category (letter): A-Z
   - Code (2 digits): 00-99
   - Subcategory (optional): .0-9, .A-Z

#### Mini ICD-10 Catalog (Demo Purposes)
Small YAML file with ~20 common codes for realistic demo:

```yaml
icd10_codes:
  J18.9:
    label: "Pneumonia, unspecified organism"
    category: "Respiratory"
  I10:
    label: "Essential (primary) hypertension"
    category: "Circulatory"
  E11.9:
    label: "Type 2 diabetes mellitus without complications"
    category: "Endocrine"
  # ... 15 more common codes
```

#### ICD-10 Field Insertion
DXCare typically has structured ICD-10 fields, not free text. HackApp must:
1. Verify target field is ICD-10-compatible
2. Insert code in correct format
3. Optionally populate separate label field
4. Handle multi-code scenarios (primary + secondary diagnoses)

---

## Non-Functional Requirements

### Performance
- **Workflow execution**: < 5 seconds end-to-end
- **Middleware response**: < 500ms (excluding external API time)
- **Hotkey detection latency**: < 100ms

### Reliability
- **External service timeout**: 30 seconds (configurable)
- **Retry policy**: 2 retries with exponential backoff
- **Graceful degradation**: Display error, don't crash

### Usability
- **Hotkey feedback**: Visual/audio confirmation of trigger
- **Error messages**: User-friendly, no stack traces
- **Configuration errors**: Clear validation messages on startup

---

## Demo Strategy (Hackathon Presentation)

### Demo Script (5 minutes)

**Slide 1: Problem** (30 sec)
- DXCare doesn't have built-in AI summarization
- Clinicians waste time on documentation

**Slide 2: Solution** (30 sec)
- HackApp = non-intrusive middleware
- Works with ANY EMR, not just DXCare

**Live Demo** (3 min):
1. Open mock DXCare (Notepad with field labels)
2. Paste clinical note: "Patient presents with cough, fever, chest infiltrates..."
3. Highlight text
4. Press CTRL+ALT+V
5. Show: Diagnosis field auto-fills with summary
6. Show: ICD-10 code field auto-fills with J18.9
7. Switch terminal: Show middleware logs (workflow executed, connector called)
8. Open `workflows.yaml`: Show how easy it is to add new workflows

**Slide 3: Architecture** (1 min)
- Show three-layer diagram
- Emphasize: Zero code for new workflows

**Q&A** (1 min)

### Wow-Factor Elements
- **Speed**: Sub-second insertion
- **Configuration**: Live-edit YAML, restart, works immediately
- **Extensibility**: "Want drug interactions? Just add 10 lines of YAML"
- **Security**: Show field whitelist blocking unauthorized field

---

## Future Enhancements (Post-Hackathon)

### Short-Term
- Multi-field context (combine multiple DXCare fields)
- Confirmation dialogs before insertion
- UI for workflow configuration (no-code editor)
- Real DXCare API integration (if vendor partnership)

### Long-Term
- Natural language workflow creation ("When I press Ctrl+Alt+X, summarize this note")
- Multi-step workflows (chained actions)
- Approval workflows (supervisor review before insertion)
- Analytics dashboard (workflow usage, success rates)
- FHIR compatibility layer
- HL7 message integration

---

## Constraints and Non-Goals (Critical)

### What HackApp IS NOT
- ❌ Not a DXCare replacement
- ❌ Not an EMR system
- ❌ Not practicing medicine (no diagnostic logic)
- ❌ Not a production-ready system
- ❌ Not HIPAA-compliant (as-is)

### What HackApp IS
- ✅ A demonstration of integration patterns
- ✅ A proof-of-concept for config-driven automation
- ✅ A framework for vendor-agnostic EMR extensions
- ✅ A hackathon-quality prototype

---

## Development Guidelines

### Code Quality
- **Separation of concerns**: No business logic in agent, no UI logic in middleware
- **Type safety**: Use Pydantic models everywhere
- **Error handling**: Defensive programming, never crash
- **Logging**: Comprehensive but PHI-free
- **Comments**: Explain "why", not "what"

### Git Workflow
- `main` branch: working prototype
- Feature branches for major components
- Commit messages: Conventional Commits format

### Testing Strategy (Minimal for Hackathon)
- **Unit tests**: Validators, transformers
- **Integration test**: Full workflow end-to-end
- **Manual testing**: Demo scenario

---

## Questions & Decisions Log

### Open Questions
1. **DXCare field detection**: Use clipboard method or window title heuristics?
   - **Decision**: Start with clipboard, add field detection if time permits

2. **ICD-10 catalog**: Embed full catalog or mini lookup?
   - **Decision**: Mini catalog (20 codes) for demo realism

3. **Multi-language support**: English only or support Spanish clinical notes?
   - **Decision**: English only for MVP

### Assumptions
- DXCare is Windows-based thick client (most common deployment)
- Clinician has single monitor (affects UI automation)
- Network latency < 100ms (localhost for hackathon)

---

## Appendix: File Structure

```
hackapp/
├── agent/
│   ├── __init__.py
│   ├── main.py                 # Entry point, hotkey listener
│   ├── context_capture.py      # Context detection logic
│   ├── inserter.py             # UI automation for data insertion
│   ├── config.py               # Agent configuration
│   └── requirements.txt
│
├── middleware/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic data models
│   ├── workflow_engine.py      # Workflow matching & execution
│   ├── connector.py            # Connector abstraction
│   ├── transformers.py         # Jinja2 template rendering
│   ├── validators.py           # ICD-10, security validation
│   ├── audit.py                # Logging (PHI-free)
│   ├── config_loader.py        # YAML config parser
│   └── requirements.txt
│
├── connectors/
│   ├── __init__.py
│   ├── base.py                 # Abstract Connector class
│   ├── rest_api.py             # REST API connector impl
│   └── voice_ai.py             # Voice AI specific connector
│
├── mock_service/
│   ├── app.py                  # Mock external API (Flask)
│   ├── data.py                 # Hardcoded lookup tables
│   └── requirements.txt
│
├── config/
│   ├── workflows.yaml          # Workflow definitions
│   ├── connectors.yaml         # Connector configurations
│   ├── icd10_mini.yaml         # Small ICD-10 catalog
│   └── .env.example            # Template for secrets
│
├── tests/
│   ├── test_workflow_engine.py
│   ├── test_validators.py
│   └── test_integration.py     # End-to-end test
│
├── docs/
│   ├── ARCHITECTURE.md         # This file
│   ├── API.md                  # Middleware API docs
│   └── DEMO.md                 # Demo script
│
├── .gitignore
├── README.md                   # Quick start guide
├── requirements.txt            # Root dependencies
└── setup.sh                    # One-command setup script
```

---

## License

MIT License (or specify if different)

---

## Contributors

[Your Team Names]

---

**End of Architecture Document**
