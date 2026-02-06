"""
HackApp Middleware - Main FastAPI Application
REST API server for workflow orchestration
"""

import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Request, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pathlib import Path

from middleware.models import (
    TriggerRequest, WorkflowResponse, HealthResponse,
    WorkflowListResponse, Context
)
from middleware.workflow_engine import WorkflowEngine
from middleware.connector import ConnectorRegistry, create_connector
from middleware.config_loader import load_all_configs
from middleware.audit import init_audit_logger, get_audit_logger
from middleware.visual_workflows import VisualWorkflow, VisualWorkflowStorage
from middleware.visual_executor import WorkflowExecutor


# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="HackApp Middleware API",
    description="Configuration-driven middleware for DXCare integration",
    version="1.0.0"
)

# CORS (allow agent to call from localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
workflow_engine: Optional[WorkflowEngine] = None
visual_workflow_storage: Optional[VisualWorkflowStorage] = None
workflow_executor: Optional[WorkflowExecutor] = None
startup_time: Optional[datetime] = None

# Picker coordination state
picker_sessions: dict = {}  # session_id -> {"field_name": str, "coordinates": Optional[tuple]}
current_session_id: Optional[str] = None

# Agent process state
agent_process = None  # Subprocess running the agent
agent_start_time: Optional[datetime] = None

# Configuration
MIDDLEWARE_TOKEN = os.getenv("MIDDLEWARE_TOKEN", "hackathon_demo_token")
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "logs/audit.log")


# ============================================================================
# Startup / Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global workflow_engine, visual_workflow_storage, workflow_executor, startup_time

    print("=" * 70)
    print("🧠 HackApp Middleware Starting...")
    print("=" * 70)

    try:
        # Initialize audit logger
        init_audit_logger(AUDIT_LOG_PATH)
        audit_logger = get_audit_logger()

        # Load configurations
        print("\n📂 Loading configurations...")
        workflows, connector_configs, icd10_catalog = load_all_configs()

        # Create connector registry
        print("\n🔌 Initializing connectors...")
        connector_registry = ConnectorRegistry()

        for name, config in connector_configs.items():
            connector = create_connector(config)
            connector_registry.register(name, connector)

        # Initialize workflow engine
        print("\n⚙️  Initializing workflow engine...")
        workflow_engine = WorkflowEngine(
            workflows=workflows,
            connector_registry=connector_registry,
            icd10_catalog=icd10_catalog
        )

        # Initialize visual workflow system
        print("\n🎨 Initializing visual workflow system...")
        visual_workflow_storage = VisualWorkflowStorage()
        workflow_executor = WorkflowExecutor()
        visual_workflows = visual_workflow_storage.list()
        print(f"✅ Loaded {len(visual_workflows)} visual workflows")

        startup_time = datetime.now()

        # Log startup
        audit_logger.log_startup(
            workflows_loaded=len(workflows),
            connectors_loaded=len(connector_configs)
        )

        print("\n" + "=" * 70)
        print("✅ HackApp Middleware Ready!")
        print(f"   📋 Workflows: {len(workflows)}")
        print(f"   🔌 Connectors: {len(connector_configs)}")
        print(f"   🏥 ICD-10 Codes: {len(icd10_catalog)}")
        print(f"   🚀 API: http://localhost:5000")
        print("=" * 70 + "\n")

        # Auto-start agent
        print("🤖 Starting agent automatically...")
        try:
            await _auto_start_agent()
        except Exception as e:
            print(f"⚠️  Failed to auto-start agent: {e}")
            print("   You can start it manually if needed")

    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


async def _auto_start_agent():
    """Helper function to auto-start agent on middleware startup"""
    global agent_process, agent_start_time
    import subprocess
    import sys
    import platform

    # Get the path to the agent main.py
    agent_path = Path(__file__).parent.parent / "agent" / "main.py"

    if not agent_path.exists():
        print(f"   ⚠️  Agent script not found: {agent_path}")
        return

    # Set up environment with PYTHONPATH
    agent_env = os.environ.copy()
    hackapp_dir = str(agent_path.parent.parent)

    # Add hackapp directory to PYTHONPATH
    if 'PYTHONPATH' in agent_env:
        agent_env['PYTHONPATH'] = f"{hackapp_dir}{os.pathsep}{agent_env['PYTHONPATH']}"
    else:
        agent_env['PYTHONPATH'] = hackapp_dir

    # Force UTF-8 encoding for Windows console
    agent_env['PYTHONIOENCODING'] = 'utf-8'

    # Windows-specific setup
    startupinfo = None
    creationflags = 0
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = 0x08000000  # CREATE_NO_WINDOW

    # Start agent process - don't capture stdout/stderr to avoid pipe blocking
    # Agent output will print directly to middleware console
    agent_process = subprocess.Popen(
        [sys.executable, "-u", str(agent_path)],
        cwd=hackapp_dir,
        env=agent_env,
        stdout=None,  # Inherit from parent (middleware console)
        stderr=None,  # Inherit from parent (middleware console)
        startupinfo=startupinfo,
        creationflags=creationflags
    )

    agent_start_time = datetime.now()

    # Give it a moment to start
    import asyncio
    await asyncio.sleep(1.0)  # Longer delay to let agent initialize

    if agent_process.poll() is not None:
        print(f"   ❌ Agent crashed immediately (exit code: {agent_process.returncode})")
        agent_process = None
        agent_start_time = None
    else:
        print(f"   ✅ Agent started successfully with PID: {agent_process.pid}")
        print(f"   📝 Agent output will appear below:")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent_process

    print("\n🛑 Shutting down HackApp Middleware...")

    # Stop agent process if running
    if agent_process is not None and agent_process.poll() is None:
        print("🛑 Stopping agent process...")
        try:
            agent_process.terminate()
            agent_process.wait(timeout=5)
            print("✅ Agent process stopped")
        except:
            agent_process.kill()
            agent_process.wait()
            print("⚠️  Agent process force killed")

    audit_logger = get_audit_logger()
    audit_logger.log_shutdown()


# ============================================================================
# Authentication
# ============================================================================

def verify_token(authorization: Optional[str] = Header(None)):
    """
    Verify bearer token

    Args:
        authorization: Authorization header

    Raises:
        HTTPException: If token is invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        if token != MIDDLEWARE_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")

    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """Root endpoint - serves dashboard"""
    dashboard_path = Path(__file__).parent / "static" / "index.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding='utf-8'), status_code=200)
    else:
        # Fallback if dashboard doesn't exist yet
        return {
            "service": "HackApp Middleware",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "dashboard": "/",
                "health": "/api/health",
                "trigger": "/api/trigger (POST)",
                "workflows": "/api/workflows",
                "audit": "/api/audit/recent",
                "docs": "/docs"
            }
        }


@app.get("/excel", response_class=HTMLResponse, tags=["Dashboard"])
async def excel_dashboard():
    """Excel automation dashboard"""
    excel_path = Path(__file__).parent / "static" / "excel.html"
    if excel_path.exists():
        return HTMLResponse(content=excel_path.read_text(encoding='utf-8'), status_code=200)
    else:
        raise HTTPException(status_code=404, detail="Excel dashboard not found")


@app.get("/api/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint

    Returns service status and statistics
    """
    if workflow_engine is None:
        return HealthResponse(
            status="unhealthy",
            workflows_loaded=0,
            connectors_active=0
        )

    uptime = (datetime.now() - startup_time).total_seconds() if startup_time else 0

    return HealthResponse(
        status="healthy",
        workflows_loaded=len(workflow_engine.workflows),
        connectors_active=len(workflow_engine.connector_registry.list()),
        uptime_seconds=uptime
    )


@app.get("/api/workflows", response_model=WorkflowListResponse, tags=["Workflows"])
async def list_workflows(authorization: str = Header(None)):
    """
    List all available workflows

    Requires authentication.
    """
    verify_token(authorization)

    if workflow_engine is None:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")

    workflows_list = []
    for hotkey, workflow in workflow_engine.workflows.items():
        workflows_list.append({
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "hotkey": hotkey,
            "connector": workflow.connector,
            "enabled": workflow.enabled
        })

    return WorkflowListResponse(
        workflows=workflows_list,
        total=len(workflows_list)
    )


@app.get("/api/audit/recent", tags=["Monitoring"])
async def get_recent_audit_logs(limit: int = 50, authorization: str = Header(None)):
    """
    Get recent audit log entries

    Requires authentication.
    """
    verify_token(authorization)

    audit_logger = get_audit_logger()
    entries = audit_logger.get_recent_entries(limit=limit)

    return {
        "entries": entries,
        "total": len(entries)
    }


@app.post("/api/trigger", response_model=WorkflowResponse, tags=["Workflows"])
async def trigger_workflow(
    request: TriggerRequest,
    authorization: str = Header(None)
):
    """
    Trigger a workflow

    This is the main endpoint called by the agent when a hotkey is pressed.

    Args:
        request: Trigger request with hotkey and context
        authorization: Bearer token

    Returns:
        WorkflowResponse with insertion instructions or error
    """
    verify_token(authorization)

    if workflow_engine is None:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")

    try:
        # Execute workflow
        response = workflow_engine.execute(
            hotkey=request.hotkey,
            context=request.context
        )

        return response

    except ValueError as e:
        # Validation or workflow errors
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Unexpected errors
        print(f"❌ Unexpected error in trigger_workflow: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Visual Workflow Endpoints
# ============================================================================

@app.get("/api/visual-workflows", tags=["Visual Workflows"])
async def list_visual_workflows(authorization: str = Header(None)):
    """List all visual workflows"""
    verify_token(authorization)

    if visual_workflow_storage is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    workflows = visual_workflow_storage.list()
    return {
        "workflows": [wf.model_dump(mode='json') for wf in workflows],
        "total": len(workflows)
    }


@app.post("/api/visual-workflows", tags=["Visual Workflows"])
async def create_visual_workflow(workflow: VisualWorkflow, authorization: str = Header(None)):
    """Create a new visual workflow"""
    verify_token(authorization)

    if visual_workflow_storage is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    try:
        created = visual_workflow_storage.create(workflow)
        return {"status": "created", "workflow": created.model_dump(mode='json')}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/visual-workflows/{workflow_id}", tags=["Visual Workflows"])
async def get_visual_workflow(workflow_id: str, authorization: str = Header(None)):
    """Get a specific visual workflow"""
    verify_token(authorization)

    if visual_workflow_storage is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    workflow = visual_workflow_storage.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    return workflow.model_dump(mode='json')


@app.put("/api/visual-workflows/{workflow_id}", tags=["Visual Workflows"])
async def update_visual_workflow(
    workflow_id: str,
    workflow: VisualWorkflow,
    authorization: str = Header(None)
):
    """Update a visual workflow"""
    verify_token(authorization)

    if visual_workflow_storage is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    try:
        updated = visual_workflow_storage.update(workflow_id, workflow)
        return {"status": "updated", "workflow": updated.model_dump(mode='json')}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/api/visual-workflows/{workflow_id}", tags=["Visual Workflows"])
async def delete_visual_workflow(workflow_id: str, authorization: str = Header(None)):
    """Delete a visual workflow"""
    verify_token(authorization)

    if visual_workflow_storage is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    visual_workflow_storage.delete(workflow_id)
    return {"status": "deleted", "workflow_id": workflow_id}


@app.post("/api/visual-workflows/{workflow_id}/execute", tags=["Visual Workflows"])
async def execute_visual_workflow(workflow_id: str, authorization: str = Header(None)):
    """Execute a visual workflow"""
    verify_token(authorization)

    if visual_workflow_storage is None or workflow_executor is None:
        raise HTTPException(status_code=503, detail="Visual workflow system not initialized")

    workflow = visual_workflow_storage.get(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    try:
        result = workflow_executor.execute(workflow.model_dump(mode='json'))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Picker Coordination Endpoints
# ============================================================================

@app.post("/api/picker/activate", tags=["Picker"])
async def activate_picker(
    request: dict,
    authorization: str = Header(None)
):
    """
    Activate coordinate picker for a specific field

    Request body:
        {
            "session_id": "unique_session_id",
            "field_name": "patient_coords" | "output_coords"
        }
    """
    verify_token(authorization)

    global current_session_id, picker_sessions

    session_id = request.get("session_id")
    field_name = request.get("field_name")

    if not session_id or not field_name:
        raise HTTPException(status_code=400, detail="Missing session_id or field_name")

    # Create/update picking session
    picker_sessions[session_id] = {
        "field_name": field_name,
        "coordinates": None
    }
    current_session_id = session_id

    return {
        "status": "picker_activated",
        "session_id": session_id,
        "field_name": field_name,
        "instruction": f"Press CTRL+ALT+C in DXCare, then click to set {field_name}"
    }


@app.post("/api/picker/coordinates", tags=["Picker"])
async def receive_coordinates(
    request: dict,
    authorization: str = Header(None)
):
    """
    Receive coordinates from agent

    Request body:
        {
            "field_name": "field_name",  # Not used if session active
            "x": 123,
            "y": 456
        }
    """
    verify_token(authorization)

    global current_session_id, picker_sessions

    x = request.get("x")
    y = request.get("y")

    if x is None or y is None:
        raise HTTPException(status_code=400, detail="Missing x or y coordinates")

    # If there's an active session, update it
    if current_session_id and current_session_id in picker_sessions:
        picker_sessions[current_session_id]["coordinates"] = (x, y)
        return {
            "status": "coordinates_received",
            "session_id": current_session_id,
            "field_name": picker_sessions[current_session_id]["field_name"],
            "x": x,
            "y": y
        }

    # Otherwise just acknowledge
    return {
        "status": "coordinates_received",
        "x": x,
        "y": y
    }


@app.get("/api/picker/status/{session_id}", tags=["Picker"])
async def get_picker_status(
    session_id: str,
    authorization: str = Header(None)
):
    """
    Poll for picker status (for dashboard)

    Returns:
        {
            "status": "waiting" | "completed",
            "field_name": "patient_coords",
            "coordinates": {"x": 123, "y": 456} | null
        }
    """
    verify_token(authorization)

    if session_id not in picker_sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    session = picker_sessions[session_id]
    coordinates = session["coordinates"]

    if coordinates:
        return {
            "status": "completed",
            "field_name": session["field_name"],
            "coordinates": {"x": coordinates[0], "y": coordinates[1]}
        }
    else:
        return {
            "status": "waiting",
            "field_name": session["field_name"],
            "coordinates": None
        }


@app.post("/api/picker/preview-ocr", tags=["Picker"])
async def preview_ocr(
    request: dict,
    authorization: str = Header(None)
):
    """
    Test OCR capture at coordinates and return screenshot preview

    Request body:
        {
            "x": 123,
            "y": 456,
            "width": 150,
            "height": 40
        }

    Returns:
        {
            "status": "success",
            "image_base64": "...",
            "ocr_text": "..."
        }
    """
    verify_token(authorization)

    try:
        import pyautogui
        import pytesseract
        import base64
        from io import BytesIO
        import re
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {str(e)}")

    try:
        x = request.get("x")
        y = request.get("y")
        width = request.get("width", 150)
        height = request.get("height", 40)

        if x is None or y is None:
            raise HTTPException(status_code=400, detail="Missing x or y coordinates")

        # Take screenshot
        screenshot = pyautogui.screenshot(region=(x, y, width, height))

        # Convert to base64
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # OCR to extract text
        ocr_text = pytesseract.image_to_string(screenshot).strip()

        # Extract numbers (same logic as executor)
        numbers = re.findall(r'\d+', ocr_text)
        extracted_id = numbers[0] if numbers else None

        return {
            "status": "success",
            "image_base64": img_base64,
            "ocr_text": ocr_text,
            "extracted_id": extracted_id,
            "coordinates": {"x": x, "y": y, "width": width, "height": height}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR preview failed: {str(e)}")


# ============================================================================
# Excel Helper Endpoints
# ============================================================================

@app.post("/api/excel/upload", tags=["Excel"])
async def upload_excel(
    file: bytes = File(...),
    filename: str = Form(...),
    authorization: str = Header(None)
):
    """
    Upload Excel file and return its full path

    Returns:
        {
            "status": "success",
            "file_path": "C:\\full\\path\\to\\file.xlsx"
        }
    """
    verify_token(authorization)

    try:
        from pathlib import Path
        import os

        # Create uploads directory if not exists
        upload_dir = Path(__file__).parent.parent / "data" / "excel_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file with original name
        file_path = upload_dir / filename

        # Write file
        with open(file_path, "wb") as f:
            f.write(file)

        return {
            "status": "success",
            "file_path": str(file_path.absolute())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/excel/columns", tags=["Excel"])
async def get_excel_columns(
    request: dict,
    authorization: str = Header(None)
):
    """
    Get column names from Excel file

    Request body:
        {
            "file_path": "C:\\path\\to\\file.xlsx",
            "sheet_name": "Sheet1" (optional)
        }

    Returns:
        {
            "status": "success",
            "columns": ["Column1", "Column2", ...],
            "file_path": "C:\\path\\to\\file.xlsx"
        }
    """
    verify_token(authorization)

    try:
        import pandas as pd
        from pathlib import Path
    except ImportError:
        raise HTTPException(status_code=500, detail="pandas not installed")

    try:
        file_path = request.get("file_path")
        sheet_name = request.get("sheet_name", 0)

        if not file_path:
            raise HTTPException(status_code=400, detail="Missing file_path")

        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        # Read Excel headers
        df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=0)
        columns = df.columns.tolist()

        return {
            "status": "success",
            "columns": columns,
            "file_path": str(path.absolute())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading Excel: {str(e)}")


# ============================================================================
# Agent Control Endpoints
# ============================================================================

@app.post("/api/agent/start", tags=["Agent"])
async def start_agent(authorization: str = Header(None)):
    """
    Start the agent process

    Returns:
        {
            "status": "started" | "already_running",
            "pid": process_id
        }
    """
    verify_token(authorization)

    global agent_process, agent_start_time

    # Check if already running
    if agent_process is not None and agent_process.poll() is None:
        return {
            "status": "already_running",
            "pid": agent_process.pid,
            "uptime_seconds": (datetime.now() - agent_start_time).total_seconds() if agent_start_time else 0
        }

    try:
        import subprocess
        import sys

        # Clean up any dead process reference
        if agent_process is not None:
            agent_process = None
            agent_start_time = None

        # Get the path to the agent main.py
        agent_path = Path(__file__).parent.parent / "agent" / "main.py"

        if not agent_path.exists():
            raise HTTPException(status_code=404, detail=f"Agent script not found: {agent_path}")

        # Start the agent process with proper error handling
        # Set up environment with PYTHONPATH
        agent_env = os.environ.copy()
        hackapp_dir = str(agent_path.parent.parent)

        # Add hackapp directory to PYTHONPATH so imports work
        if 'PYTHONPATH' in agent_env:
            agent_env['PYTHONPATH'] = f"{hackapp_dir}{os.pathsep}{agent_env['PYTHONPATH']}"
        else:
            agent_env['PYTHONPATH'] = hackapp_dir

        # Force UTF-8 encoding for Windows console to handle emoji characters
        agent_env['PYTHONIOENCODING'] = 'utf-8'

        # Use CREATE_NEW_CONSOLE on Windows to prevent terminal issues
        import platform
        startupinfo = None
        creationflags = 0

        if platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # CREATE_NO_WINDOW flag to hide console window
            creationflags = 0x08000000  # CREATE_NO_WINDOW

        agent_process = subprocess.Popen(
            [sys.executable, "-u", str(agent_path)],  # -u for unbuffered output
            cwd=hackapp_dir,  # Run from hackapp/ directory
            env=agent_env,  # Pass modified environment
            stdout=None,  # Inherit from parent (don't capture to avoid blocking)
            stderr=None,  # Inherit from parent
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        agent_start_time = datetime.now()

        # Give it a moment to start and check if it immediately crashes
        import asyncio
        await asyncio.sleep(1.0)

        if agent_process.poll() is not None:
            # Process died immediately
            print(f"❌ Agent crashed immediately (exit code: {agent_process.returncode})")
            agent_process = None
            agent_start_time = None
            raise HTTPException(
                status_code=500,
                detail=f"Agent crashed immediately after start (exit code: {agent_process.returncode})"
            )

        print(f"✅ Agent started successfully with PID: {agent_process.pid}")

        return {
            "status": "started",
            "pid": agent_process.pid,
            "message": "Agent process started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start agent: {e}")
        import traceback
        traceback.print_exc()
        agent_process = None
        agent_start_time = None
        raise HTTPException(status_code=500, detail=f"Failed to start agent: {str(e)}")


@app.post("/api/agent/stop", tags=["Agent"])
async def stop_agent(authorization: str = Header(None)):
    """
    Stop the agent process

    Returns:
        {
            "status": "stopped" | "not_running"
        }
    """
    verify_token(authorization)

    global agent_process, agent_start_time

    # Check if running
    if agent_process is None or agent_process.poll() is not None:
        agent_process = None
        agent_start_time = None
        return {
            "status": "not_running",
            "message": "Agent was not running"
        }

    try:
        # Terminate the process
        agent_process.terminate()

        # Wait up to 5 seconds for graceful shutdown
        try:
            agent_process.wait(timeout=5)
        except:
            # Force kill if it doesn't terminate gracefully
            agent_process.kill()
            agent_process.wait()

        pid = agent_process.pid
        agent_process = None
        agent_start_time = None

        print(f"✅ Agent stopped (PID: {pid})")

        return {
            "status": "stopped",
            "message": "Agent process stopped successfully"
        }

    except Exception as e:
        print(f"❌ Failed to stop agent: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to stop agent: {str(e)}")


@app.get("/api/agent/status", tags=["Agent"])
async def get_agent_status(authorization: str = Header(None)):
    """
    Get agent process status

    Returns:
        {
            "running": true/false,
            "pid": process_id (if running),
            "uptime_seconds": seconds (if running)
        }
    """
    verify_token(authorization)

    global agent_process, agent_start_time

    # Check if process is running
    if agent_process is not None and agent_process.poll() is None:
        uptime = (datetime.now() - agent_start_time).total_seconds() if agent_start_time else 0
        return {
            "running": True,
            "pid": agent_process.pid,
            "uptime_seconds": uptime
        }
    else:
        # If process died, try to get error output
        error_output = None
        if agent_process is not None:
            try:
                stdout, stderr = agent_process.communicate(timeout=0.1)
                error_output = stderr if stderr else stdout
            except:
                pass
            agent_process = None
            agent_start_time = None

        return {
            "running": False,
            "pid": None,
            "uptime_seconds": 0,
            "last_error": error_output[:500] if error_output else None
        }


@app.get("/api/agent/logs", tags=["Agent"])
async def get_agent_logs(authorization: str = Header(None)):
    """
    Get recent agent output (stdout/stderr)

    Returns last output from agent process
    """
    verify_token(authorization)

    global agent_process

    if agent_process is None:
        return {
            "running": False,
            "stdout": None,
            "stderr": None,
            "message": "Agent is not running"
        }

    try:
        # Non-blocking read of available output
        import select
        import os

        stdout_data = ""
        stderr_data = ""

        # Try to read stdout if available
        if agent_process.stdout:
            try:
                # This is a simplified approach - in production you'd use a proper logging system
                stdout_data = "Output capture not implemented in streaming mode"
            except:
                pass

        return {
            "running": agent_process.poll() is None,
            "pid": agent_process.pid if agent_process else None,
            "stdout": stdout_data,
            "stderr": stderr_data,
            "message": "Agent logs (limited capture)"
        }

    except Exception as e:
        return {
            "running": False,
            "error": str(e)
        }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    print(f"❌ Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


# ============================================================================
# Run Server
# ============================================================================

def main():
    """Start the middleware server"""
    import uvicorn

    print("\n🚀 Starting HackApp Middleware Server...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
