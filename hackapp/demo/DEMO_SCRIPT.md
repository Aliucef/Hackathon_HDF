# HackApp - 5-Minute Demo Script

**For Hackathon Presentation**

---

## Setup (Before Demo - 2 minutes)

### Terminal Setup
Open 3 terminals:
1. **Terminal 1**: Mock Service
2. **Terminal 2**: Middleware
3. **Terminal 3**: Agent

### Start Services
```bash
# Terminal 1
cd hackapp && python3 mock_service/app.py

# Terminal 2
cd hackapp && python3 middleware/main.py

# Terminal 3
cd hackapp && python3 agent/main.py
```

### Prepare DXCare Simulator
Open Notepad with this template:

```
═══════════════════════════════════════════════════════════
        DXCare - Patient Chart (SIMULATOR)
═══════════════════════════════════════════════════════════
Patient: Jean Dupont
ID: HDF-12345
Date: 2026-02-05
═══════════════════════════════════════════════════════════

CLINICAL NOTES:




═══════════════════════════════════════════════════════════

DIAGNOSIS (Text):


═══════════════════════════════════════════════════════════

DIAGNOSIS (ICD-10 Code):


═══════════════════════════════════════════════════════════
HackApp Integration Active | Press CTRL+ALT+V
═══════════════════════════════════════════════════════════
```

---

## Demo Flow (3 minutes)

### Slide 1: The Problem (30 seconds)

**SAY:**
> "DXCare doesn't allow direct integration of AI tools. Clinicians waste time on manual documentation. Our hospital needs AI-powered clinical summarization, but we can't modify DXCare."

**SHOW:** Slide with problem statement

---

### Slide 2: The Solution (30 seconds)

**SAY:**
> "We built HackApp - a configuration-driven middleware that works as a 'Man-in-the-Middle'. It intercepts hotkeys, calls external AI services, and auto-fills DXCare fields. Zero code changes to DXCare."

**SHOW:** Architecture diagram (3 layers)

---

### Live Demo (90 seconds)

#### Part 1: Paste Clinical Note

**SAY:**
> "Doctor is documenting a patient consultation in DXCare..."

**DO:**
1. Click into "CLINICAL NOTES" section in Notepad
2. Paste this text:
   ```
   Patient presents with persistent cough for 5 days, fever 102°F, chest pain on deep breathing, and difficulty breathing. Physical exam reveals crackles in right lower lung. Chest X-ray shows infiltrates in right lower lobe consistent with bacterial pneumonia. Patient appears acutely ill.
   ```

#### Part 2: Trigger AI Summarization

**SAY:**
> "The doctor selects the clinical note... and presses CTRL+ALT+V. Watch what happens..."

**DO:**
1. Select all the clinical note text (Ctrl+A)
2. Press **CTRL+ALT+V**
3. **PAUSE** - let everyone watch the magic

#### Part 3: Show Results

**SAY:**
> "In less than 3 seconds:
> - AI analyzed the clinical note
> - Generated a structured summary
> - Suggested an ICD-10 diagnosis code
> - And automatically filled both fields!"

**POINT TO:**
- Diagnosis (Text): "Pneumonia with respiratory symptoms..."
- Diagnosis (ICD-10 Code): "J18.9"

**SHOW** terminals:
- Mock Service log: "Processed clinical summary request"
- Middleware log: "Workflow executed successfully"
- Agent log: "Inserted 2 fields"

---

### Slide 3: The Architecture (30 seconds)

**SAY:**
> "Here's how it works behind the scenes:"

**SHOW:** Architecture slide with flow:
```
1. Agent captures hotkey (even when DXCare is active)
2. Middleware matches hotkey to workflow
3. Calls external Voice AI service
4. Validates ICD-10 code format
5. Returns insertion instructions
6. Agent auto-types into fields
```

**EMPHASIZE:**
- "Configuration-driven - add new workflows via YAML, no code!"
- "Works with ANY EMR, not just DXCare"
- "Security-aware - field whitelists, PHI-free logging"

---

### Slide 4: Extensibility (30 seconds)

**SAY:**
> "Want to add drug interaction checking? Just add 10 lines of YAML:"

**SHOW:** `workflows.yaml` file with new workflow

**SAY:**
> "No programming required. Perfect for rapid iteration."

---

## Q&A (1.5 minutes)

### Anticipated Questions

**Q: Does this require DXCare API access?**
**A:** No! We use UI automation (keyboard simulation). Works with any application.

**Q: What about security?**
**A:**
- Field whitelists prevent unauthorized writes
- PHI-free audit logs
- Bearer token authentication
- ICD-10 format validation

**Q: Can this work in production?**
**A:** Yes, with enhancements:
- Switch to FHIR APIs instead of UI automation
- Add HTTPS + proper auth
- Deploy with Docker
- Add confirmation dialogs

**Q: How long to add a new workflow?**
**A:** 5-10 minutes to edit YAML config. No code changes needed.

**Q: Does it work with other EMRs?**
**A:** Yes! Epic, Cerner, Allscripts - anything with keyboard input.

---

## Backup Demo (If Tech Fails)

### Fallback Plan A: Video Recording
- Have pre-recorded demo video ready
- Show terminals + Notepad in action
- Narrate over video

### Fallback Plan B: Manual Walkthrough
- Show code structure
- Walk through config files
- Explain architecture with slides
- Show API documentation (FastAPI /docs)

---

## Key Talking Points

### Innovation
- ✅ "Man-in-the-Middle" pattern for legacy EMRs
- ✅ Configuration-driven (zero-code extensibility)
- ✅ Works with ANY application (not DXCare-specific)

### Technical Excellence
- ✅ Clean 3-layer architecture
- ✅ Proper validation (ICD-10 format, field whitelists)
- ✅ PHI-free audit logs (HIPAA-aware)
- ✅ Error handling & retries

### Practical Value
- ✅ Saves clinician time (seconds vs minutes)
- ✅ Reduces documentation errors
- ✅ Enables rapid AI integration
- ✅ Extensible to many use cases

---

## Post-Demo

### If Time Permits:
- Show FastAPI auto-docs: http://localhost:5000/docs
- Open `workflows.yaml` and explain config
- Demonstrate adding a second workflow live

### Final Statement:
> "HackApp proves that legacy EMRs can be extended with modern AI tools without vendor lock-in. It's fast, secure, and extensible. Thank you!"

---

## Demo Checklist

- [ ] All 3 services running and healthy
- [ ] Notepad template ready
- [ ] Clinical note text copied
- [ ] Terminals visible on screen
- [ ] Backup video ready (if needed)
- [ ] Slides loaded
- [ ] Timer set (5 minutes)

---

**Good luck!** 🍀
