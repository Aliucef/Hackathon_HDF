# HackApp - Project Implementation Plan
## Phase-by-Phase Execution Map

**Start Date**: 2026-02-05
**Target**: Working prototype for hackathon demo
**Estimated Total Time**: 3-4 hours

---

## 📋 PHASE OVERVIEW

```
Phase 0: Project Setup          [15 min] ✅ Foundation
Phase 1: Data Models & Config   [30 min] 🧱 Core Structure
Phase 2: Middleware API         [60 min] 🧠 Brain
Phase 3: Client Agent           [45 min] 🖱️ Hands
Phase 4: Mock External Service  [20 min] 🤖 External Services
Phase 5: Integration & Testing  [30 min] 🔗 End-to-End
Phase 6: Demo Setup & Polish    [30 min] 🎬 Presentation Ready

Total: ~3.5 hours to working demo
```

---

## 🗺️ DETAILED PHASE MAP

### **PHASE 0: Project Setup & Structure** ⏱️ 15 minutes

**Goal**: Create clean project structure with all directories and base files.

**Deliverables:**
- [ ] Directory structure created
- [ ] requirements.txt files for each component
- [ ] .gitignore configured
- [ ] .env.example template
- [ ] README placeholders

**Files to Create:**
```
hackapp/
├── agent/
│   ├── __init__.py
│   ├── main.py
│   ├── hotkey_listener.py
│   ├── context_capture.py
│   ├── inserter.py
│   ├── config.py
│   └── requirements.txt
├── middleware/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── workflow_engine.py
│   ├── connector.py
│   ├── transformers.py
│   ├── validators.py
│   ├── audit.py
│   └── requirements.txt
├── connectors/
│   ├── __init__.py
│   ├── base.py
│   └── voice_ai_connector.py
├── mock_service/
│   ├── __init__.py
│   ├── app.py
│   ├── data.py
│   └── requirements.txt
├── config/
│   ├── workflows.yaml
│   ├── connectors.yaml
│   └── icd10_mini.yaml
├── tests/
│   └── test_basic.py
├── .gitignore
├── .env.example
└── setup.sh
```

**Success Criteria:**
- ✅ All directories exist
- ✅ All __init__.py files created
- ✅ Can import modules without errors

---

### **PHASE 1: Data Models & Configuration** ⏱️ 30 minutes

**Goal**: Define all data structures and configuration schemas.

**Dependencies**: Phase 0 complete

**Deliverables:**
- [ ] Pydantic models for all data structures
- [ ] YAML configuration loader
- [ ] Sample workflow configuration
- [ ] Sample connector configuration
- [ ] ICD-10 mini catalog (20 codes)

**Files to Implement:**

1. **middleware/models.py**
   - `Context` - Input from agent
   - `WorkflowConfig` - Workflow definition
   - `ConnectorConfig` - Connector configuration
   - `InsertionInstruction` - Output to agent
   - `WorkflowResponse` - Complete response
   - `ICD10Code` - ICD-10 data structure

2. **config/workflows.yaml**
   - At least 1 complete workflow: `voice_summary_icd10`
   - Input validation rules
   - Connector reference
   - Request template
   - Response mappings
   - Output instructions

3. **config/connectors.yaml**
   - `voice_ai` connector definition
   - Base URL, auth config
   - Endpoint definitions

4. **config/icd10_mini.yaml**
   - 20 common ICD-10 codes with labels

5. **middleware/config_loader.py**
   - Load YAML files
   - Validate against Pydantic schemas
   - Return typed config objects

**Success Criteria:**
- ✅ All models have type hints
- ✅ YAML configs load without errors
- ✅ Can validate sample workflow config
- ✅ ICD-10 regex validation works

**Test:**
```python
from middleware.config_loader import load_workflows
workflows = load_workflows('config/workflows.yaml')
assert len(workflows) > 0
assert workflows[0].workflow_id == 'voice_summary_icd10'
```

---

### **PHASE 2: Middleware API** ⏱️ 60 minutes

**Goal**: Build the core brain - workflow engine, connectors, validation.

**Dependencies**: Phase 1 complete

**Deliverables:**
- [ ] FastAPI application with endpoints
- [ ] Workflow engine (hotkey matcher)
- [ ] Connector abstraction layer
- [ ] Request/response transformer (Jinja2)
- [ ] ICD-10 validator
- [ ] Audit logger
- [ ] Health check endpoint

**Files to Implement:**

1. **middleware/main.py** (FastAPI app)
   - `POST /api/trigger` - Main workflow endpoint
   - `GET /api/health` - Health check
   - `GET /api/workflows` - List loaded workflows
   - Error handling middleware
   - CORS configuration
   - Bearer token authentication

2. **middleware/workflow_engine.py**
   ```python
   class WorkflowEngine:
       def __init__(self, config_path: str)
       def match_hotkey(self, hotkey: str) -> WorkflowConfig
       def execute(self, workflow: WorkflowConfig, context: Context) -> WorkflowResponse
       def validate_input(self, workflow, context)
   ```

3. **middleware/connector.py**
   ```python
   class Connector(ABC):
       @abstractmethod
       def execute(self, request: dict) -> dict

   class ConnectorRegistry:
       def register(name: str, connector: Connector)
       def get(name: str) -> Connector

   class RestApiConnector(Connector):
       def execute(self, request: dict) -> dict
   ```

4. **middleware/transformers.py**
   ```python
   class TemplateRenderer:
       def render_request(template: str, context: dict) -> str
       def extract_response(mappings: dict, response: dict) -> dict
   ```

5. **middleware/validators.py**
   ```python
   class ICD10Validator:
       PATTERN = re.compile(r'^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$')
       def validate(code: str) -> ValidationResult

   class FieldWhitelistValidator:
       def validate(field: str, allowed: list) -> bool
   ```

6. **middleware/audit.py**
   ```python
   class AuditLogger:
       def log_workflow_execution(workflow_id, user_id, status, duration)
       # NO clinical data logged
   ```

**Success Criteria:**
- ✅ Server starts without errors
- ✅ `/api/health` returns 200
- ✅ Can match hotkey to workflow
- ✅ ICD-10 validation works (J18.9 valid, XYZ invalid)
- ✅ Template rendering works with Jinja2

**Test:**
```bash
# Start server
python middleware/main.py

# Test in another terminal
curl http://localhost:5000/api/health
# Expected: {"status": "healthy", "workflows_loaded": 1}

curl -X POST http://localhost:5000/api/trigger \
  -H "Content-Type: application/json" \
  -d '{"hotkey": "CTRL+ALT+V", "context": {...}}'
# Expected: {"status": "success", "insertions": [...]}
```

---

### **PHASE 3: Client Agent** ⏱️ 45 minutes

**Goal**: Build desktop agent with hotkey listening and UI automation.

**Dependencies**: Phase 2 complete (middleware running)

**Deliverables:**
- [ ] Global hotkey listener
- [ ] Context capture (clipboard/selected text)
- [ ] HTTP client to call middleware
- [ ] UI automation for insertion
- [ ] Error handling and notifications
- [ ] Configuration file

**Files to Implement:**

1. **agent/main.py**
   ```python
   def main():
       # Load config
       # Start hotkey listener
       # Wait for triggers
       # Handle Ctrl+C gracefully
   ```

2. **agent/hotkey_listener.py**
   ```python
   from pynput import keyboard

   class HotkeyListener:
       def __init__(self, hotkeys: dict):
           self.hotkeys = hotkeys  # {'<ctrl>+<alt>+v': callback}

       def start(self):
           # Start global hotkey listener

       def on_hotkey(self, hotkey: str):
           # Trigger workflow
   ```

3. **agent/context_capture.py**
   ```python
   import pyperclip
   import pygetwindow as gw

   class ContextCapture:
       def get_active_window_title(self) -> str
       def get_clipboard_text(self) -> str
       def get_selected_text(self) -> str  # Via clipboard backup
       def capture(self) -> Context
   ```

4. **agent/inserter.py**
   ```python
   import pyautogui
   import time

   class FieldInserter:
       def insert(self, instruction: InsertionInstruction):
           if instruction.mode == "replace":
               pyautogui.hotkey('ctrl', 'a')
               pyautogui.press('delete')

           pyautogui.write(instruction.content, interval=0.01)

           if instruction.navigation:
               self.navigate(instruction.navigation)

       def navigate(self, nav: str):
           # Handle "tab_3" -> press Tab 3 times
           if nav.startswith("tab_"):
               count = int(nav.split("_")[1])
               pyautogui.press('tab', presses=count, interval=0.1)
   ```

5. **agent/config.py**
   ```python
   MIDDLEWARE_URL = "http://localhost:5000"
   MIDDLEWARE_TOKEN = "hackathon_demo_token"

   HOTKEYS = {
       '<ctrl>+<alt>+v': 'voice_summary',
       '<ctrl>+<alt>+d': 'drug_interaction'
   }
   ```

6. **agent/middleware_client.py**
   ```python
   import requests

   class MiddlewareClient:
       def trigger_workflow(self, hotkey: str, context: Context) -> WorkflowResponse:
           response = requests.post(
               f"{MIDDLEWARE_URL}/api/trigger",
               json={"hotkey": hotkey, "context": context.dict()},
               headers={"Authorization": f"Bearer {MIDDLEWARE_TOKEN}"}
           )
           return WorkflowResponse(**response.json())
   ```

**Success Criteria:**
- ✅ Agent starts without errors
- ✅ Can detect global hotkeys (test with Notepad open)
- ✅ Can capture selected text
- ✅ Can call middleware successfully
- ✅ Can auto-type into active window

**Test:**
```bash
# Terminal 1: Start middleware
python middleware/main.py

# Terminal 2: Start agent
python agent/main.py
# Output: "HackApp Agent started. Press CTRL+ALT+V to test..."

# Terminal 3: Open Notepad, type text, select it, press CTRL+ALT+V
# Expected: Text gets replaced with middleware response
```

---

### **PHASE 4: Mock External Service** ⏱️ 20 minutes

**Goal**: Create simple mock API for Voice AI service.

**Dependencies**: None (can be done in parallel with Phase 2-3)

**Deliverables:**
- [ ] Flask API with `/api/clinical_summary` endpoint
- [ ] Keyword-based mock logic
- [ ] Returns realistic JSON responses
- [ ] Small lookup table for common diagnoses

**Files to Implement:**

1. **mock_service/app.py**
   ```python
   from flask import Flask, request, jsonify
   from data import get_mock_summary

   app = Flask(__name__)

   @app.route('/api/clinical_summary', methods=['POST'])
   def clinical_summary():
       data = request.json
       text = data.get('text', '')

       # Mock AI processing
       result = get_mock_summary(text)

       return jsonify(result)

   if __name__ == '__main__':
       app.run(port=5001, debug=True)
   ```

2. **mock_service/data.py**
   ```python
   import re

   DIAGNOSES = {
       'pneumonia': {
           'keywords': ['cough', 'fever', 'chest', 'infiltrate', 'pneumonia'],
           'summary': 'Pneumonia with respiratory symptoms and radiological findings',
           'icd10': {'code': 'J18.9', 'label': 'Pneumonia, unspecified organism'}
       },
       'hypertension': {
           'keywords': ['blood pressure', 'hypertension', 'BP', 'elevated pressure'],
           'summary': 'Essential hypertension without complications',
           'icd10': {'code': 'I10', 'label': 'Essential (primary) hypertension'}
       },
       'diabetes': {
           'keywords': ['diabetes', 'glucose', 'blood sugar', 'glycemia'],
           'summary': 'Type 2 diabetes mellitus without complications',
           'icd10': {'code': 'E11.9', 'label': 'Type 2 diabetes mellitus without complications'}
       }
   }

   def get_mock_summary(text: str) -> dict:
       text_lower = text.lower()

       # Simple keyword matching
       for diagnosis, data in DIAGNOSES.items():
           matches = sum(1 for kw in data['keywords'] if kw in text_lower)
           if matches >= 2:
               return {
                   'summary': data['summary'],
                   'icd10': data['icd10'],
                   'confidence': min(0.95, 0.6 + matches * 0.1),
                   'processing_time_ms': 234
               }

       # Default fallback
       return {
           'summary': 'Clinical presentation documented, further evaluation needed',
           'icd10': {'code': 'R69', 'label': 'Illness, unspecified'},
           'confidence': 0.5,
           'processing_time_ms': 123
       }
   ```

**Success Criteria:**
- ✅ Flask server starts on port 5001
- ✅ Can call endpoint via curl/Postman
- ✅ Returns valid JSON with summary + ICD-10

**Test:**
```bash
# Start mock service
python mock_service/app.py

# Test in another terminal
curl -X POST http://localhost:5001/api/clinical_summary \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient presents with persistent cough, fever, chest infiltrates"}'

# Expected:
# {
#   "summary": "Pneumonia with respiratory symptoms...",
#   "icd10": {"code": "J18.9", "label": "Pneumonia..."},
#   "confidence": 0.87
# }
```

---

### **PHASE 5: Integration & Testing** ⏱️ 30 minutes

**Goal**: Wire everything together and test end-to-end.

**Dependencies**: Phases 2, 3, 4 complete

**Deliverables:**
- [ ] All services communicate correctly
- [ ] End-to-end workflow works
- [ ] Error handling tested
- [ ] Basic integration test

**Tasks:**

1. **Connect Middleware to Mock Service**
   - Update `config/connectors.yaml` with correct URL
   - Test connector can call mock service
   - Verify response parsing

2. **Connect Agent to Middleware**
   - Update agent config with middleware URL
   - Test authentication works
   - Test context is sent correctly

3. **End-to-End Test**
   ```python
   # tests/test_integration.py
   def test_full_workflow():
       # 1. Start all services (middleware, mock_service)
       # 2. Simulate agent request
       # 3. Verify response contains insertions
       # 4. Check audit log entry created
   ```

4. **Error Handling Tests**
   - Invalid hotkey → proper error message
   - External service timeout → graceful failure
   - Invalid ICD-10 code → validation error
   - Network error → retry logic

5. **Manual Demo Test**
   - Open Notepad
   - Add field labels: "Clinical Notes: ____", "ICD-10: ____"
   - Type sample clinical note
   - Select text
   - Press CTRL+ALT+V
   - Verify auto-insertion works

**Success Criteria:**
- ✅ All 3 services running simultaneously
- ✅ Hotkey triggers full workflow
- ✅ Data flows: Agent → Middleware → Mock Service → Middleware → Agent
- ✅ Auto-insertion works in Notepad
- ✅ Takes < 5 seconds end-to-end

---

### **PHASE 6: Demo Setup & Polish** ⏱️ 30 minutes

**Goal**: Prepare impressive demo and presentation materials.

**Dependencies**: Phase 5 complete

**Deliverables:**
- [ ] DXCare simulator (Notepad or HTML form)
- [ ] Demo script document
- [ ] Startup script (one command to start everything)
- [ ] Presentation slides (key points)
- [ ] Demo video recording (optional)

**Tasks:**

1. **Create DXCare Simulator**

   **Option A: Notepad Template** (Simplest)
   ```
   ════════════════════════════════════════════════
   DXCare - Patient Chart Simulator
   Patient: Jean Dupont | ID: 12345 | Date: 2026-02-05
   ════════════════════════════════════════════════

   Clinical Notes:
   [Paste clinical note here, select text, press CTRL+ALT+V]




   Diagnosis (Text):


   Diagnosis (ICD-10 Code):


   ════════════════════════════════════════════════
   HackApp Integration Active | Press CTRL+ALT+V
   ════════════════════════════════════════════════
   ```

   **Option B: HTML Form** (More Impressive)
   ```html
   <!-- demo/dxcare_simulator.html -->
   <!DOCTYPE html>
   <html>
   <head>
       <title>DXCare - Patient Chart Simulator</title>
       <style>
           body { font-family: Arial; padding: 20px; background: #f0f0f0; }
           .chart { background: white; padding: 20px; border-radius: 8px; max-width: 800px; margin: auto; }
           label { font-weight: bold; display: block; margin-top: 15px; }
           textarea, input { width: 100%; padding: 8px; margin-top: 5px; }
           .header { background: #0066cc; color: white; padding: 10px; margin: -20px -20px 20px; }
           .footer { margin-top: 20px; padding: 10px; background: #e8f4f8; text-align: center; }
       </style>
   </head>
   <body>
       <div class="chart">
           <div class="header">
               <h2>DXCare - Patient Chart</h2>
               <p>Patient: Jean Dupont | ID: 12345 | Date: 2026-02-05</p>
           </div>

           <label>Clinical Notes:</label>
           <textarea id="clinical_notes" rows="10" placeholder="Enter or paste clinical notes here..."></textarea>

           <label>Diagnosis (Text):</label>
           <input type="text" id="diagnosis_text" placeholder="Auto-filled by HackApp">

           <label>Diagnosis (ICD-10 Code):</label>
           <input type="text" id="diagnosis_code" placeholder="Auto-filled by HackApp" maxlength="7">

           <div class="footer">
               <strong>HackApp Integration Active</strong><br>
               Select text in Clinical Notes and press <kbd>CTRL+ALT+V</kbd>
           </div>
       </div>
   </body>
   </html>
   ```

2. **Create Demo Script**
   ```markdown
   # DEMO.md

   ## 5-Minute Demo Script

   ### Setup (30 seconds)
   1. Open 3 terminals
   2. Terminal 1: `python mock_service/app.py`
   3. Terminal 2: `python middleware/main.py`
   4. Terminal 3: `python agent/main.py`
   5. Open DXCare simulator (HTML or Notepad)

   ### Demo Flow (3 minutes)
   1. **Introduce problem** (30 sec)
      - "DXCare doesn't have AI integration"
      - "Clinicians spend too much time on documentation"

   2. **Show HackApp** (30 sec)
      - "We built a middleware that doesn't modify DXCare"
      - "Configuration-driven, works with any EMR"

   3. **Live Demo** (90 sec)
      - Paste clinical note: "Patient presents with persistent cough, fever 39°C, chest pain. Chest X-ray shows infiltrates in right lower lobe."
      - Select text
      - Press CTRL+ALT+V
      - **WATCH:** Fields auto-fill with summary + ICD-10
      - Show middleware logs (workflow executed)

   4. **Show Architecture** (30 sec)
      - 3-layer diagram slide
      - Emphasize: zero code for new workflows
      - Show `workflows.yaml` - just add 10 lines for new workflow

   ### Q&A (1.5 minutes)
   ```

3. **Create Startup Script**
   ```bash
   # setup.sh
   #!/bin/bash

   echo "🚀 HackApp - Starting all services..."

   # Check Python version
   python3 --version || { echo "Python 3 not found"; exit 1; }

   # Install dependencies
   echo "📦 Installing dependencies..."
   pip install -r agent/requirements.txt
   pip install -r middleware/requirements.txt
   pip install -r mock_service/requirements.txt

   # Start services in background
   echo "🤖 Starting mock external service..."
   python3 mock_service/app.py &
   MOCK_PID=$!

   sleep 2

   echo "🧠 Starting middleware..."
   python3 middleware/main.py &
   MIDDLEWARE_PID=$!

   sleep 2

   echo "🖱️  Starting agent..."
   python3 agent/main.py &
   AGENT_PID=$!

   echo ""
   echo "✅ All services running!"
   echo "   Mock Service PID: $MOCK_PID"
   echo "   Middleware PID: $MIDDLEWARE_PID"
   echo "   Agent PID: $AGENT_PID"
   echo ""
   echo "📝 Open DXCare simulator and press CTRL+ALT+V"
   echo "🛑 Press Ctrl+C to stop all services"

   # Trap Ctrl+C to kill all processes
   trap "kill $MOCK_PID $MIDDLEWARE_PID $AGENT_PID" EXIT

   wait
   ```

4. **Test Demo Multiple Times**
   - Practice demo flow
   - Ensure it works reliably
   - Time it (should be under 3 minutes)
   - Prepare for failure scenarios

5. **Polish**
   - Add console colors/emojis for visibility
   - Clear, helpful error messages
   - Add "Starting..." / "Ready!" status messages

**Success Criteria:**
- ✅ Can start all services with one command
- ✅ Demo works consistently (3/3 attempts)
- ✅ Demo completes in < 3 minutes
- ✅ Impressive to watch (data appears "magically")

---

## 🎯 CRITICAL PATH

**These must be done in order:**
```
Phase 0 → Phase 1 → Phase 2 → Phase 3
                    ↓
                 Phase 4 (parallel)
                    ↓
              Phase 5 → Phase 6
```

**Can be parallelized:**
- Phase 2 (Middleware) and Phase 4 (Mock Service) are independent
- Documentation can be written alongside implementation

---

## ✅ SUCCESS METRICS

**Minimum Viable Demo (Must-Have):**
- [ ] 1 workflow fully functional (voice_summary_icd10)
- [ ] Agent captures context
- [ ] Middleware calls external service
- [ ] Auto-insertion works
- [ ] Can demo in < 3 minutes

**Nice-to-Have (Time Permitting):**
- [ ] 2+ workflows
- [ ] HTML DXCare simulator
- [ ] Visual notifications in agent
- [ ] Pretty terminal output with colors
- [ ] Demo video recording

**Stretch Goals (If Extra Time):**
- [ ] Web UI for workflow configuration
- [ ] Real-time logs dashboard
- [ ] Multiple external service connectors
- [ ] FHIR API integration (if credentials provided)

---

## 🚨 RISK MANAGEMENT

### Potential Blockers

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **UI automation doesn't work** | Low | High | Test early (Phase 3), have clipboard fallback |
| **Hotkey library issues** | Low | High | Test multiple libraries (pynput, keyboard) |
| **Services can't communicate** | Medium | High | Test localhost connectivity early |
| **Demo fails during presentation** | Low | Critical | Practice 5+ times, have video backup |
| **Windows permission issues** | Medium | Medium | Run as administrator, document in README |

### Contingency Plans

**If UI automation fails:**
- Fallback: Copy to clipboard, user pastes manually
- Still impressive, just less "magical"

**If hotkeys don't work:**
- Fallback: CLI command to trigger workflow
- Still demonstrates architecture

**If external service fails:**
- Hardcode mock responses in middleware
- Same visual result

---

## 📊 PROGRESS TRACKING

**We'll use this checklist during implementation:**

### Phase 0: Setup ⏱️ 15 min
- [ ] Project structure created
- [ ] All requirements.txt files
- [ ] Git initialized

### Phase 1: Models ⏱️ 30 min
- [ ] Pydantic models defined
- [ ] YAML configs created
- [ ] Config loader works

### Phase 2: Middleware ⏱️ 60 min
- [ ] FastAPI app running
- [ ] Workflow engine implemented
- [ ] Connectors working
- [ ] Validators working

### Phase 3: Agent ⏱️ 45 min
- [ ] Hotkey listener working
- [ ] Context capture working
- [ ] Middleware client working
- [ ] UI automation working

### Phase 4: Mock Service ⏱️ 20 min
- [ ] Flask app running
- [ ] Mock logic implemented
- [ ] Returns realistic data

### Phase 5: Integration ⏱️ 30 min
- [ ] All services running together
- [ ] End-to-end workflow works
- [ ] Error handling tested

### Phase 6: Demo ⏱️ 30 min
- [ ] DXCare simulator ready
- [ ] Demo script written
- [ ] Startup script works
- [ ] Demo practiced

---

## 🎯 CURRENT STATUS

**Phase**: Ready to start Phase 0
**Time**: 15:00 estimated for first phase
**Next Action**: Create project structure

---

**Ready to begin Phase 0?** Let's build this! 🚀
