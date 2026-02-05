 🧪 Step-by-Step Testing Guide                                                                                                                      
  
  Let me walk you through testing HackApp from scratch!                                                                                                 
  ---                                                                                                                                                
  STEP 1: Check Prerequisites (2 minutes)

  Open a terminal and verify:

  # Check Python version (need 3.9+)
  python3 --version

  # Navigate to project directory
  cd /mnt/c/Users/Aliuc/OneDrive/Desktop/Hackathon_HDF

  # Verify structure
  ls hackapp/

  Expected output: Should show agent/, middleware/, mock_service/, config/ folders

  ---
  STEP 2: Install Dependencies (3-5 minutes)

  # Install all required packages
  pip install --user -r hackapp/agent/requirements.txt
  pip install --user -r hackapp/middleware/requirements.txt
  pip install --user -r hackapp/mock_service/requirements.txt

  If you get errors, try:
  python3 -m pip install --user pynput pyautogui pyperclip requests
  python3 -m pip install --user fastapi uvicorn pydantic pyyaml jinja2 jsonpath-ng
  python3 -m pip install --user flask flask-cors

  ---
  STEP 3: Start Services (One at a time)

  Terminal 1: Start Mock External Service

  cd /mnt/c/Users/Aliuc/OneDrive/Desktop/Hackathon_HDF/hackapp
  python3 mock_service/app.py

  Expected output:
  ======================================================================
  🤖 HackApp Mock External Service Starting...
  ======================================================================

  📍 Endpoints:
     • http://localhost:5001/api/clinical_summary
     • http://localhost:5001/health

  ✅ Mock service ready for requests!
  ======================================================================

   * Running on http://0.0.0.0:5001

  ✅ Leave this terminal running

  ---
  Terminal 2: Start Middleware (Open new terminal)

  cd /mnt/c/Users/Aliuc/OneDrive/Desktop/Hackathon_HDF/hackapp
  python3 middleware/main.py

  Expected output:
  ======================================================================
  🧠 HackApp Middleware Starting...
  ======================================================================

  📂 Loading configurations...
  ✅ Loaded 2 workflows
  ✅ Loaded 2 connectors
  ✅ Loaded 20 ICD-10 codes

  🔌 Initializing connectors...
  ✅ Registered connector: voice_ai
  ✅ Registered connector: drug_checker

  ⚙️  Initializing workflow engine...
  ✅ Workflow Engine initialized with 1 workflows

  ======================================================================
  ✅ HackApp Middleware Ready!
     📋 Workflows: 1
     🔌 Connectors: 2
     🏥 ICD-10 Codes: 20
     🚀 API: http://localhost:5000
  ======================================================================

  INFO:     Started server process
  INFO:     Uvicorn running on http://0.0.0.0:5000

  ✅ Leave this terminal running

  ---
  Terminal 3: Start Agent (Open new terminal)

  cd /mnt/c/Users/Aliuc/OneDrive/Desktop/Hackathon_HDF/hackapp
  python3 agent/main.py

  Expected output:
  ======================================================================
  🖱️  HackApp Agent - Desktop Client
  ======================================================================

  ✅ Agent components initialized

  📡 Checking middleware connection...
     ✅ Middleware is online and healthy

  📋 Loaded 1 workflow(s):
     • CTRL+ALT+V: Voice AI Clinical Summary with ICD-10

  🎹 Starting hotkey listener...
     Registered hotkeys:
        • CTRL+ALT+V
     ✅ Hotkey listener active!

  ======================================================================
  ✅ HackApp Agent is Ready!
  ======================================================================

  💡 Usage:
     1. Open DXCare (or text editor for demo)
     2. Select clinical text
     3. Press a registered hotkey (e.g., CTRL+ALT+V)
     4. Watch fields auto-fill!

  🛑 Press Ctrl+C to exit
  ======================================================================

  ✅ Leave this terminal running

  ---
  STEP 4: Prepare DXCare Simulator (1 minute)

  Open Notepad (or any text editor) and paste this:

  ═══════════════════════════════════════════════════════════════════
          DXCare - Patient Chart (SIMULATOR)
  ═══════════════════════════════════════════════════════════════════
  Patient: Jean Dupont
  ID: HDF-12345
  Date: 2026-02-05
  ═══════════════════════════════════════════════════════════════════

  CLINICAL NOTES:
  Patient presents with persistent cough for 5 days, fever 102°F, chest pain on deep breathing, and difficulty breathing. Physical exam reveals      
  crackles in right lower lung. Chest X-ray shows infiltrates in right lower lobe consistent with bacterial pneumonia.


  ═══════════════════════════════════════════════════════════════════

  DIAGNOSIS (Text):


  ═══════════════════════════════════════════════════════════════════

  DIAGNOSIS (ICD-10 Code):


  ═══════════════════════════════════════════════════════════════════
  Press CTRL+ALT+V to auto-fill diagnosis
  ═══════════════════════════════════════════════════════════════════

  ---
  STEP 5: Test the Workflow! (30 seconds)

  In Notepad:

  1. Select the clinical note text (the paragraph starting with "Patient presents...")
    - Click and drag to highlight, OR
    - Triple-click the paragraph, OR
    - Click at start, hold Shift, click at end
  2. Copy it (Ctrl+C) - this puts it in clipboard
  3. Press CTRL+ALT+V (hold Ctrl, hold Alt, press V)
  4. Watch the magic! ✨

  ---
  EXPECTED BEHAVIOR:

  What You Should See:

  1. In Agent Terminal (Terminal 3):
  ======================================================================
  🎹 Hotkey detected: CTRL+ALT+V
  ======================================================================

  📸 Capturing context...
     Selected text: Patient presents with persistent cough for 5 days...

  📡 Calling middleware...
     Endpoint: http://localhost:5000/api/trigger
     ✅ Response received (450ms)
     Workflow: voice_summary_icd10
     Status: success

     📝 Received 2 insertion(s)

     📝 Inserting into DiagnosisText...
        Mode: replace
        Content: Pneumonia with respiratory symptoms and radiological findings...
        ✅ Inserted successfully

     📝 Inserting into DiagnosisCode...
        Mode: replace
        Content: J18.9
        ✅ Inserted successfully

  ✅ All 2 field(s) inserted successfully!
  ======================================================================
  2. In Notepad:
    - Cursor moves to "DIAGNOSIS (Text):" field
    - Text appears: "Pneumonia with respiratory symptoms and radiological findings consistent with lower respiratory tract infection"
    - Cursor moves down (presses Tab 3 times)
    - Text appears: "J18.9"
  3. In Middleware Terminal (Terminal 2):
  🚀 Executing workflow: voice_summary_icd10
     📤 Request: {'text': 'Patient presents with...'}...
     📥 Response: {'summary': 'Pneumonia...', 'icd10': {'code': 'J18.9'}}...
     🔍 Extracted: ['summary', 'icd10_code', 'icd10_label', 'confidence']
     ✅ Built 2 insertion instructions
  4. In Mock Service Terminal (Terminal 1):
  ✅ Processed clinical summary request:
     Input length: 234 chars
     Diagnosis: J18.9
     Confidence: 0.92

  ---
  STEP 6: Verify Results

  In Notepad, you should now see:

  DIAGNOSIS (Text):
  Pneumonia with respiratory symptoms and radiological findings consistent with lower respiratory tract infection

  ═══════════════════════════════════════════════════════════════════

  DIAGNOSIS (ICD-10 Code):
  J18.9

  ✅ SUCCESS! The system works!

  ---
  TROUBLESHOOTING

  Problem 1: "Cannot connect to middleware"

  Check:
  # Test middleware health
  curl http://localhost:5000/api/health

  Expected: {"status":"healthy","workflows_loaded":1,...}

  If not working:
  - Make sure Terminal 2 is still running
  - Check for errors in Terminal 2
  - Try restarting middleware

  ---
  Problem 2: "Hotkey not detected"

  Possible causes:
  - Another app is using CTRL+ALT+V
  - Need to run with admin/sudo permissions
  - pynput not installed correctly

  Fix:
  # On Windows - Run terminal as Administrator
  # On Linux:
  sudo python3 agent/main.py

  Test hotkey listener separately:
  python3 hackapp/agent/hotkey_listener.py
  # Press CTRL+ALT+V - should print "Hotkey pressed!"

  ---
  Problem 3: "No text selected" warning

  Cause: You didn't copy the text first

  Fix:
  1. Select the clinical note text in Notepad
  2. Press Ctrl+C to copy (important!)
  3. Then press CTRL+ALT+V

  ---
  Problem 4: "Text not inserting"

  Cause: Notepad not the active window

  Fix:
  1. After pressing CTRL+ALT+V, immediately click into Notepad
  2. Make sure cursor is in the "DIAGNOSIS (Text):" area
  3. Don't touch keyboard/mouse while it's typing

  ---
  Problem 5: Import errors

  Error: ModuleNotFoundError: No module named 'pynput'

  Fix:
  # Install missing module
  pip install --user pynput

  # Or install all at once:
  pip install --user pynput pyautogui pyperclip requests fastapi uvicorn pydantic pyyaml flask

  ---
  QUICK TEST CHECKLIST

  - Python 3.9+ installed
  - All dependencies installed (pip install ...)
  - Terminal 1: Mock service running (port 5001)
  - Terminal 2: Middleware running (port 5000)
  - Terminal 3: Agent running (hotkeys active)
  - Notepad open with template
  - Clinical text selected AND copied (Ctrl+C)
  - Pressed CTRL+ALT+V
  - Text auto-filled in Notepad

  ---
  ALTERNATIVE: Quick Health Check

  Before full test, verify each service:

  # Test 1: Mock Service
  curl http://localhost:5001/health
  # Expected: {"status":"healthy","service":"mock_external_service"}

  # Test 2: Middleware
  curl http://localhost:5000/api/health
  # Expected: {"status":"healthy","workflows_loaded":1,...}

  # Test 3: Mock API call
  curl -X POST http://localhost:5001/api/clinical_summary \
    -H "Content-Type: application/json" \
    -d '{"text":"Patient has cough and fever"}'
  # Expected: {"summary":"...","icd10":{"code":"J18.9",...}}

  # Test 4: Middleware trigger (manual)
  curl -X POST http://localhost:5000/api/trigger \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer hackathon_demo_token" \
    -d '{"hotkey":"CTRL+ALT+V","context":{"selected_text":"Patient has pneumonia"}}'
  # Expected: {"status":"success","insertions":[...],...}

  ---
  VIDEO WALKTHROUGH (If still stuck)

  If you encounter issues, I can help debug! Just tell me:
  1. Which step failed?
  2. What error message did you see?
  3. What terminal showed the error?

  ---
  SUCCESS = Ready for Demo! 🎉

  Once this test works, you're ready to present. The demo will be even more impressive with live typing!

  Need help with any step? Ask me! 🚀