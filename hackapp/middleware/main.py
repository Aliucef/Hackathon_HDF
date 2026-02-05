"""
HackApp Middleware - Main FastAPI Application
REST API server for workflow orchestration
"""

import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional

from .models import (
    TriggerRequest, WorkflowResponse, HealthResponse,
    WorkflowListResponse, Context
)
from .workflow_engine import WorkflowEngine
from .connector import ConnectorRegistry, create_connector
from .config_loader import load_all_configs
from .audit import init_audit_logger, get_audit_logger


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
startup_time: Optional[datetime] = None

# Configuration
MIDDLEWARE_TOKEN = os.getenv("MIDDLEWARE_TOKEN", "hackathon_demo_token")
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "logs/audit.log")


# ============================================================================
# Startup / Shutdown
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global workflow_engine, startup_time

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

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "service": "HackApp Middleware",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "trigger": "/api/trigger (POST)",
            "workflows": "/api/workflows",
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
