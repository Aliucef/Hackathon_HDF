"""
HackApp Middleware - Main FastAPI Application
REST API server for workflow orchestration
"""

import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Request
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

    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("\n🛑 Shutting down HackApp Middleware...")
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
        return HTMLResponse(content=dashboard_path.read_text(), status_code=200)
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
