# HackApp - Configurable Middleware for DXCare Integration

**Hackathon Project**: Non-intrusive automation layer for EMR systems

---

## 🎯 What Is This?

HackApp enables clinicians to trigger AI-powered workflows (clinical summarization, ICD-10 suggestions, decision support) via **global hotkeys** while working in DXCare, with **automatic data insertion** back into DXCare fields.

**Key Innovation**: Zero-code workflow configuration - add new automations by editing YAML files, no programming required.

---

## 📚 Documentation

1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete system design, data models, and implementation plan
2. **[DXCARE_INTEGRATION_TECHNICAL.md](./DXCARE_INTEGRATION_TECHNICAL.md)** - Technical proof that hotkeys + auto-insertion work

---

## ✅ Core Questions Answered

### Can we create hotkeys that work when DXCare is active?
**YES** - Using global keyboard hooks (`pynput` library). Works with any application.

### Can we write data back into DXCare through HackApp?
**YES** - Using UI automation (`pyautogui`). Simulates keyboard input into active fields.

### Do we need DXCare API access?
**NO** - Works with system-level automation. DXCare doesn't even know we exist.

---

## 🏗️ Architecture (3 Layers)

```
┌─────────────────┐
│  CLIENT AGENT   │  Hotkey listener + UI automation
│  (Desktop App)  │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   MIDDLEWARE    │  Workflow engine + connector layer
│  (REST API)     │  Configuration-driven logic
└────────┬────────┘
         │ REST APIs
         ▼
┌─────────────────┐
│    EXTERNAL     │  Voice AI, Decision Support, etc.
│    SERVICES     │
└─────────────────┘
```

---

## 🚀 Quick Start (Recommended Build Order)

### Phase 1: Foundation (30-45 min)
- [ ] Create project structure
- [ ] Define Pydantic data models
- [ ] Build YAML config loader
- [ ] Create sample workflow config

### Phase 2: Middleware Core (1-1.5 hours)
- [ ] FastAPI REST API (`/api/trigger`, `/api/health`)
- [ ] Workflow engine (hotkey → workflow matcher)
- [ ] Connector abstraction
- [ ] Response transformer
- [ ] ICD-10 validator

### Phase 3: Client Agent (45 min)
- [ ] Global hotkey listener (`pynput`)
- [ ] Context capture (clipboard/selected text)
- [ ] Middleware API client
- [ ] UI automation for insertion (`pyautogui`)

### Phase 4: Mock Service + Demo (30 min)
- [ ] Mock external API (Flask)
- [ ] Simulated DXCare (Notepad or HTML form)
- [ ] Demo script
- [ ] Presentation slides

**Total Time**: ~3-3.5 hours to working prototype

---

## 🎬 Demo Flow

1. Clinician working in "DXCare" (Notepad with field labels)
2. Selects clinical note text: *"Patient presents with persistent cough, fever, chest pain. Chest X-ray shows infiltrates."*
3. Presses **CTRL+ALT+V**
4. HackApp Agent:
   - Captures selected text
   - Calls middleware
5. Middleware:
   - Matches hotkey to "voice_summary_icd10" workflow
   - Calls mock Voice AI service
   - Receives: `{ "summary": "Pneumonia...", "icd10": "J18.9" }`
   - Returns insertion instructions
6. Agent auto-types into DXCare fields:
   - **DiagnosisText**: "Pneumonia with respiratory symptoms"
   - **DiagnosisCode**: "J18.9"
7. Clinician reviews and saves

**Wow Factor**: Data appears automatically, no copy-paste, sub-second execution.

---

## 📁 Project Structure

```
hackapp/
├── agent/                     # Desktop client (Python)
│   ├── main.py               # Hotkey listener + orchestrator
│   ├── context_capture.py    # Get selected text, window info
│   ├── inserter.py           # UI automation (pyautogui)
│   └── requirements.txt
│
├── middleware/                # Core brain (FastAPI)
│   ├── main.py               # REST API server
│   ├── models.py             # Pydantic data models
│   ├── workflow_engine.py    # Config-driven workflow execution
│   ├── connector.py          # Abstract connector + registry
│   ├── transformers.py       # Jinja2 templates
│   ├── validators.py         # ICD-10, security validation
│   ├── audit.py              # PHI-free logging
│   └── requirements.txt
│
├── connectors/               # External service integrations
│   └── voice_ai.py           # Voice AI connector
│
├── mock_service/             # Simulated external API
│   └── app.py                # Flask app with mock responses
│
├── config/                   # Zero-code workflow definitions
│   ├── workflows.yaml        # Workflow configs
│   ├── connectors.yaml       # Connector configs
│   └── icd10_mini.yaml       # Small ICD-10 lookup table
│
├── tests/
│   ├── test_workflow_engine.py
│   └── test_integration.py
│
├── docs/
│   ├── ARCHITECTURE.md       # Full system design
│   ├── DXCARE_INTEGRATION_TECHNICAL.md
│   └── DEMO.md               # Demo script for presentation
│
└── README.md                 # This file
```

---

## 🔧 Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Agent** | Python 3.9+ | Cross-platform, great libraries |
| **Hotkeys** | `pynput` | Global keyboard hooks |
| **UI Automation** | `pyautogui` | Simulates typing into DXCare |
| **Middleware** | FastAPI | Fast, auto-docs, async support |
| **Config** | YAML + Pydantic | Human-readable, type-safe |
| **Templates** | Jinja2 | Dynamic request/response transform |
| **Mock Service** | Flask | Minimal, quick to build |

---

## 🔐 Security (Hackathon Scope)

- ✅ Token-based auth (agent ↔ middleware)
- ✅ Field whitelist (only allowed fields can be written)
- ✅ ICD-10 format validation
- ✅ PHI-free audit logs
- ⚠️ HTTPS optional (localhost OK for demo)
- ⚠️ No user authentication (single clinician assumed)

**Not production-ready** - this is a proof-of-concept.

---

## 📋 Example Configuration

### Workflow Definition (`config/workflows.yaml`)
```yaml
- workflow_id: voice_summary_icd10
  name: "AI Clinical Summary + ICD-10"
  hotkey: CTRL+ALT+V
  enabled: true

  input:
    source: selected_text
    validation:
      min_length: 10
      max_length: 5000

  connector: voice_ai

  request:
    template: |
      Summarize this clinical note and suggest ICD-10 code:
      {{ input_text }}

  response:
    mappings:
      summary: $.summary
      icd10_code: $.icd10.code

  output:
    - type: text
      target_field: DiagnosisText
      content: "{{ summary }}"
      mode: replace

    - type: icd10
      target_field: DiagnosisCode
      content: "{{ icd10_code }}"
      mode: replace

  security:
    allowed_fields: [DiagnosisText, DiagnosisCode]
```

**Adding a new workflow**: Just add another YAML block. No code changes needed.

---

## 🧪 Testing Strategy

### Quick Proof-of-Concept Tests

**Test 1: Hotkey Detection**
```python
# Run this, then press CTRL+ALT+V in any app
from pynput import keyboard

with keyboard.GlobalHotKeys({'<ctrl>+<alt>+v': lambda: print("Hotkey works!")}) as h:
    h.join()
```

**Test 2: Auto-Typing**
```python
# Run this, switch to Notepad within 3 seconds
import pyautogui, time
time.sleep(3)
pyautogui.write("Hello from HackApp!")
```

### Integration Test
1. Start mock service: `python mock_service/app.py`
2. Start middleware: `python middleware/main.py`
3. Start agent: `python agent/main.py`
4. Open Notepad (simulated DXCare)
5. Type clinical note, select text, press CTRL+ALT+V
6. Verify auto-insertion works

---

## 🎯 Success Criteria

### Must-Have (MVP)
- [x] Architecture documented
- [ ] Global hotkeys work
- [ ] One complete workflow (voice summary + ICD-10)
- [ ] Config-driven (no hardcoded logic)
- [ ] Auto-insertion into fields
- [ ] End-to-end demo working

### Nice-to-Have (Time Permitting)
- [ ] Multiple workflows
- [ ] Web-based DXCare simulator
- [ ] Visual feedback during insertion
- [ ] Error handling UI
- [ ] Demo video recording

---

## 🚫 Non-Goals (Don't Build These)

- ❌ Real DXCare APIs (we don't have access)
- ❌ Full ICD-10 database (use mini lookup table)
- ❌ Medical AI (use mock responses)
- ❌ Production security (hackathon-level is fine)
- ❌ UI for workflow editing (YAML files are enough)

---

## 🤝 Team Roles (Suggested)

| Role | Responsibilities | Time |
|------|-----------------|------|
| **Backend Dev** | Middleware API, workflow engine | 2 hours |
| **Desktop Dev** | Agent (hotkeys + UI automation) | 1.5 hours |
| **Integration** | Mock service, config files, testing | 1 hour |
| **Demo/Docs** | Presentation, demo script, polish | 1 hour |

**Can be done by 1-2 people** if needed.

---

## 📞 Next Steps

1. **Read the docs**:
   - `ARCHITECTURE.md` for full system design
   - `DXCARE_INTEGRATION_TECHNICAL.md` for technical proof

2. **Run proof-of-concept tests** (see Testing Strategy above)

3. **Choose tech stack** (recommend: Python + FastAPI + pynput + pyautogui)

4. **Start coding**:
   - Begin with Phase 1 (data models + config loader)
   - Build incrementally, test each layer

5. **Build demo** (Notepad or HTML form simulating DXCare)

6. **Prepare presentation** (5-min demo + architecture slide)

---

## 💡 Key Selling Points (For Judges)

1. **Zero-code extensibility** - New workflows via YAML, not programming
2. **Vendor-agnostic** - Works with ANY EMR, not just DXCare
3. **Non-intrusive** - No DXCare modifications needed
4. **Healthcare-aware** - ICD-10 validation, PHI-free logging
5. **Composable architecture** - Swap connectors, workflows independently
6. **Real-world applicable** - Similar to how Epic MyChart integrations work

---

## 📄 License

MIT License (or specify)

---

## 👥 Team

[Your Names Here]

---

## 🎉 Let's Build This!

**Estimated time to working demo**: 3-3.5 hours

**Current status**: Architecture documented ✅, ready to code ⚡

Questions? Check the detailed docs or ask!
