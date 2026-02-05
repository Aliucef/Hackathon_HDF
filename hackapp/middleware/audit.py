"""
Audit Logger
PHI-free logging for workflow executions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import AuditLogEntry


class AuditLogger:
    """
    Logs workflow executions WITHOUT any clinical data

    CRITICAL: Never log:
    - Clinical text (notes, diagnoses, symptoms)
    - Patient identifiers (names, IDs, SSNs)
    - API request/response bodies
    - Any PHI/PII

    Only log:
    - Workflow metadata (ID, connector, timestamp)
    - Success/failure status
    - Execution time
    - Error codes (not error messages with data)
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize audit logger

        Args:
            log_file: Path to audit log file. If None, logs to console only.
        """
        self.logger = logging.getLogger('hackapp.audit')
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s [AUDIT] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_format = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
                datefmt='%Y-%m-%dT%H:%M:%S'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)

    def log_workflow_execution(
        self,
        workflow_id: str,
        connector: str,
        status: str,
        execution_time_ms: int,
        user_id: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        """
        Log a workflow execution

        Args:
            workflow_id: Workflow identifier
            connector: Connector name used
            status: 'success', 'error', or 'timeout'
            execution_time_ms: Execution time in milliseconds
            user_id: User identifier (if available)
            error_code: Error code (NOT error message with data)
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            workflow_id=workflow_id,
            user_id=user_id,
            connector=connector,
            status=status,
            execution_time_ms=execution_time_ms,
            error_code=error_code
        )

        # Create JSON log entry (safe for parsing)
        log_data = {
            "event": "workflow_execution",
            "workflow_id": entry.workflow_id,
            "connector": entry.connector,
            "status": entry.status,
            "execution_time_ms": entry.execution_time_ms,
            "user_id": entry.user_id,
            "error_code": entry.error_code
        }

        self.logger.info(json.dumps(log_data))

    def log_error(
        self,
        workflow_id: str,
        error_code: str,
        error_type: str
    ):
        """
        Log an error (without sensitive data)

        Args:
            workflow_id: Workflow identifier
            error_code: Error code
            error_type: Type of error (validation, timeout, etc.)
        """
        log_data = {
            "event": "workflow_error",
            "workflow_id": workflow_id,
            "error_code": error_code,
            "error_type": error_type
        }

        self.logger.error(json.dumps(log_data))

    def log_startup(self, workflows_loaded: int, connectors_loaded: int):
        """
        Log system startup

        Args:
            workflows_loaded: Number of workflows loaded
            connectors_loaded: Number of connectors loaded
        """
        log_data = {
            "event": "system_startup",
            "workflows_loaded": workflows_loaded,
            "connectors_loaded": connectors_loaded
        }

        self.logger.info(json.dumps(log_data))

    def log_shutdown(self):
        """Log system shutdown"""
        log_data = {
            "event": "system_shutdown"
        }

        self.logger.info(json.dumps(log_data))


# ============================================================================
# Global logger instance
# ============================================================================

# Will be initialized by main.py
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def init_audit_logger(log_file: Optional[str] = None):
    """
    Initialize the global audit logger

    Args:
        log_file: Path to audit log file
    """
    global _audit_logger
    _audit_logger = AuditLogger(log_file)


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing audit logger...")
    print("=" * 60)

    # Test audit logging
    logger = AuditLogger()

    print("\n1. Logging successful workflow:")
    logger.log_workflow_execution(
        workflow_id="voice_summary_icd10",
        connector="voice_ai",
        status="success",
        execution_time_ms=1234,
        user_id="clinician_123"
    )

    print("\n2. Logging failed workflow:")
    logger.log_workflow_execution(
        workflow_id="drug_interaction_check",
        connector="drug_checker",
        status="error",
        execution_time_ms=567,
        user_id="clinician_456",
        error_code="VALIDATION_ERROR"
    )

    print("\n3. Logging error:")
    logger.log_error(
        workflow_id="voice_summary_icd10",
        error_code="INVALID_ICD10",
        error_type="validation"
    )

    print("\n4. Logging startup:")
    logger.log_startup(workflows_loaded=2, connectors_loaded=3)

    print("\n✅ Audit logger tests complete!")
    print("\nNOTE: No PHI/clinical data was logged ✅")
