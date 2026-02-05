# HackApp - Quick Start Guide

**Get the demo running in 5 minutes!**

---

## Prerequisites

- Python 3.9+ installed
- Windows (for UI automation) or Linux/Mac (limited functionality)

---

## Installation

### 1. Install Dependencies

```bash
# Navigate to project root
cd /path/to/Hackathon_HDF

# Install all dependencies
pip install -r hackapp/agent/requirements.txt
pip install -r hackapp/middleware/requirements.txt
pip install -r hackapp/mock_service/requirements.txt
```

### 2. Verify Installation

```bash
python3 --version  # Should be 3.9+
pip list | grep -E "(fastapi|pynput|flask)"
```

---

## Running the Demo

### Option A: Automatic Start (Recommended)

```bash
# From project root
./setup.sh
```

This starts all 3 services in the background.

### Option B: Manual Start (3 Terminals)

**Terminal 1 - Mock External Service:**
```bash
cd hackapp
python3 mock_service/app.py
```

**Terminal 2 - Middleware:**
```bash
cd hackapp
python3 middleware/main.py
```

**Terminal 3 - Agent:**
```bash
cd hackapp
python3 agent/main.py
```

---

## Testing the System

### 1. Prepare DXCare Simulator

Open Notepad (or any text editor) and paste this template:

```
========================================
DXCare - Patient Chart Simulator
Patient: Jean Dupont | ID: 12345
========================================

Clinical Notes:
[Paste clinical text here]




Diagnosis (Text):


Diagnosis (ICD-10 Code):


========================================
```

### 2. Test Clinical Summarization

1. **Copy sample text:**
   ```
   Patient presents with persistent cough, fever 102F, chest pain, and difficulty breathing. Chest X-ray shows infiltrates in right lower lobe consistent with pneumonia.
   ```

2. **In Notepad:**
   - Select the text above
   - Press **CTRL+ALT+V**

3. **Expected Result:**
   - "Diagnosis (Text)" fills with AI summary
   - "Diagnosis (ICD-10 Code)" fills with J18.9

4. **Watch the logs** in each terminal to see the workflow execute!

---

## Sample Clinical Notes for Testing

### Test Case 1: Pneumonia
```
Patient presents with persistent cough, fever 102F, chest pain. Chest X-ray shows infiltrates.
```
**Expected ICD-10**: J18.9

### Test Case 2: Hypertension
```
Patient has elevated blood pressure readings: 160/95 mmHg. History of essential hypertension.
```
**Expected ICD-10**: I10

### Test Case 3: Diabetes
```
Patient reports increased thirst and urination. Fasting blood glucose: 185 mg/dL. Diagnosis: Type 2 diabetes mellitus.
```
**Expected ICD-10**: E11.9

### Test Case 4: Back Pain
```
Patient complains of chronic low back pain in lumbar region, worsens with movement. No radiation to legs.
```
**Expected ICD-10**: M54.5

---

## Troubleshooting

### "Cannot connect to middleware"
- Check middleware is running on port 5000
- Visit http://localhost:5000/api/health to verify

### "Hotkeys not working"
- On Windows: Run as Administrator
- On Linux: Check input group permissions
- Verify no other app is using the same hotkey

### "Text not inserting"
- Make sure Notepad/text editor is the active window
- Click into the target field before pressing hotkey
- Check agent logs for errors

### "ICD-10 validation error"
- Check mock service is returning valid format
- Visit http://localhost:5001/health to verify

---

## Configuration

### Change Hotkeys

Edit `hackapp/agent/config.py`:
```python
HOTKEYS = {
    '<ctrl>+<alt>+v': 'CTRL+ALT+V',  # Voice summarization
    '<ctrl>+<alt>+x': 'CTRL+ALT+X',  # Your custom hotkey
}
```

### Add New Workflow

Edit `hackapp/config/workflows.yaml` - just add a new workflow block!

### Change Mock Responses

Edit `hackapp/mock_service/data.py` to customize diagnoses.

---

## API Documentation

### Middleware API
- **Health**: `GET http://localhost:5000/api/health`
- **Trigger**: `POST http://localhost:5000/api/trigger`
- **Workflows**: `GET http://localhost:5000/api/workflows`
- **Docs**: http://localhost:5000/docs (FastAPI auto-docs)

### Mock External Service
- **Health**: `GET http://localhost:5001/health`
- **Summarize**: `POST http://localhost:5001/api/clinical_summary`

---

## Architecture Overview

```
┌─────────────────┐
│  CLIENT AGENT   │  Desktop app (Python)
│  (Port: N/A)    │  - Hotkey listener
└────────┬────────┘  - UI automation
         │
         ▼ HTTP
┌─────────────────┐
│   MIDDLEWARE    │  FastAPI server
│  (Port: 5000)   │  - Workflow engine
└────────┬────────┘  - Validation
         │
         ▼ HTTP
┌─────────────────┐
│ EXTERNAL SERVICE│  Flask mock API
│  (Port: 5001)   │  - Clinical AI simulation
└─────────────────┘
```

---

## Next Steps

1. **Demo for judges**: Show the live workflow
2. **Add workflows**: Edit YAML configs (no code needed!)
3. **Integrate real APIs**: Update connector configs
4. **Deploy**: Consider Docker for production

---

## Need Help?

- Check logs in `./logs/` directory
- Review documentation in project root
- See `ARCHITECTURE.md` for technical details

---

**Happy Hacking!** 🚀
