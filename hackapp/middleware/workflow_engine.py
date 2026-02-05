"""
Workflow Engine
Core orchestration logic for executing workflows
"""

import time
from typing import List, Dict, Any, Optional
from middleware.models import (
    WorkflowConfig, Context, WorkflowResponse, InsertionInstruction
)
from middleware.connector import ConnectorRegistry, ConnectorError
from middleware.transformers import TemplateRenderer, ResponseExtractor, OutputBuilder
from middleware.validators import (
    ICD10Validator, FieldWhitelistValidator, InputValidator, SecurityValidator
)
from middleware.audit import get_audit_logger


class WorkflowEngine:
    """
    Executes workflows based on configuration

    Flow:
    1. Match hotkey to workflow
    2. Validate input
    3. Render request template
    4. Call external connector
    5. Extract response data
    6. Validate response
    7. Build output instructions
    8. Return to agent
    """

    def __init__(
        self,
        workflows: List[WorkflowConfig],
        connector_registry: ConnectorRegistry,
        icd10_catalog: Optional[Dict] = None
    ):
        """
        Initialize workflow engine

        Args:
            workflows: List of workflow configurations
            connector_registry: Registry of connectors
            icd10_catalog: Optional ICD-10 catalog for validation
        """
        self.workflows = {wf.hotkey: wf for wf in workflows if wf.enabled}
        self.connector_registry = connector_registry
        self.icd10_catalog = icd10_catalog or {}

        # Initialize components
        self.template_renderer = TemplateRenderer()
        self.response_extractor = ResponseExtractor()
        self.output_builder = OutputBuilder()

        # Validators
        self.icd10_validator = ICD10Validator(self.icd10_catalog)
        self.input_validator = InputValidator()
        self.security_validator = SecurityValidator()

        self.audit_logger = get_audit_logger()

        print(f"✅ Workflow Engine initialized with {len(self.workflows)} workflows")

    def match_hotkey(self, hotkey: str) -> Optional[WorkflowConfig]:
        """
        Find workflow matching hotkey

        Args:
            hotkey: Hotkey combination (e.g., "CTRL+ALT+V")

        Returns:
            WorkflowConfig if found, None otherwise
        """
        # Normalize hotkey (uppercase, consistent format)
        hotkey_normalized = hotkey.upper().replace(" ", "")

        for workflow_hotkey, workflow in self.workflows.items():
            workflow_hotkey_normalized = workflow_hotkey.upper().replace(" ", "")
            if workflow_hotkey_normalized == hotkey_normalized:
                return workflow

        return None

    def validate_input(self, workflow: WorkflowConfig, context: Context) -> None:
        """
        Validate workflow input

        Args:
            workflow: Workflow configuration
            context: Input context

        Raises:
            ValueError: If validation fails
        """
        # Get input text based on source
        if workflow.input.source == "selected_text":
            input_text = context.selected_text or ""
        elif workflow.input.source == "clipboard":
            input_text = context.clipboard_text or ""
        elif workflow.input.source == "active_field_text":
            input_text = context.selected_text or ""  # Fallback
        else:
            input_text = ""

        # Validate length if specified
        if workflow.input.validation:
            min_length = workflow.input.validation.get('min_length')
            max_length = workflow.input.validation.get('max_length')

            result = self.input_validator.validate_text_length(
                input_text, min_length, max_length
            )

            if not result.valid:
                raise ValueError(result.error)

    def execute(self, hotkey: str, context: Context) -> WorkflowResponse:
        """
        Execute workflow triggered by hotkey

        Args:
            hotkey: Hotkey that was pressed
            context: Context captured by agent

        Returns:
            WorkflowResponse with insertion instructions or error

        Raises:
            ValueError: If workflow not found or validation fails
        """
        start_time = time.time()

        try:
            # 1. Match hotkey to workflow
            workflow = self.match_hotkey(hotkey)
            if not workflow:
                raise ValueError(f"No workflow found for hotkey: {hotkey}")

            print(f"\n🚀 Executing workflow: {workflow.workflow_id}")

            # 2. Validate input
            self.validate_input(workflow, context)

            # 3. Prepare input data for template
            input_data = self._prepare_input_data(workflow, context)

            # 4. Render request template
            request_template = workflow.request.template
            try:
                request_json = self.template_renderer.render_json(
                    request_template, input_data
                )
            except ValueError:
                # Try rendering as string if JSON fails
                request_str = self.template_renderer.render(
                    request_template, input_data
                )
                request_json = {"text": request_str}

            print(f"   📤 Request: {str(request_json)[:100]}...")

            # 5. Get connector and call external service
            connector = self.connector_registry.get(workflow.connector)
            try:
                response_data = connector.execute(
                    endpoint=list(connector.config.endpoints.keys())[0],  # First endpoint
                    request_data=request_json,
                    method=workflow.request.method
                )
            except ConnectorError as e:
                self._log_error(workflow, context, e.error_code, int((time.time() - start_time) * 1000))
                raise ValueError(f"Connector error: {e}")

            print(f"   📥 Response: {str(response_data)[:100]}...")

            # 6. Extract response data
            extracted = self.response_extractor.extract(
                response_data, workflow.response.mappings
            )

            print(f"   🔍 Extracted: {list(extracted.keys())}")

            # 7. Validate response
            self._validate_response(workflow, extracted)

            # 8. Build output instructions
            instructions = self.output_builder.build_instructions(
                workflow.output, extracted
            )

            print(f"   ✅ Built {len(instructions)} insertion instructions")

            # 9. Log success
            execution_time = int((time.time() - start_time) * 1000)
            self.audit_logger.log_workflow_execution(
                workflow_id=workflow.workflow_id,
                connector=workflow.connector,
                status="success",
                execution_time_ms=execution_time,
                user_id=context.user_id
            )

            return WorkflowResponse(
                status="success",
                workflow_id=workflow.workflow_id,
                insertions=instructions,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            # Try to get workflow_id for logging
            workflow_id = workflow.workflow_id if ('workflow' in locals() and workflow) else "unknown"

            if ('workflow' in locals() and workflow) and 'context' in locals():
                self._log_error(workflow, context, "EXECUTION_ERROR", execution_time)

            return WorkflowResponse(
                status="error",
                workflow_id=workflow_id,
                insertions=[],
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _prepare_input_data(self, workflow: WorkflowConfig, context: Context) -> Dict[str, Any]:
        """
        Prepare input data for template rendering

        Args:
            workflow: Workflow configuration
            context: Input context

        Returns:
            Dictionary with input_text and other context
        """
        # Get input text based on source
        if workflow.input.source == "selected_text":
            input_text = context.selected_text or ""
        elif workflow.input.source == "clipboard":
            input_text = context.clipboard_text or ""
        else:
            input_text = context.selected_text or context.clipboard_text or ""

        return {
            "input_text": input_text,
            "user_id": context.user_id,
            "window_title": context.window_title,
            "active_field": context.active_field
        }

    def _validate_response(self, workflow: WorkflowConfig, extracted_data: Dict[str, Any]) -> None:
        """
        Validate response data

        Args:
            workflow: Workflow configuration
            extracted_data: Extracted response data

        Raises:
            ValueError: If validation fails
        """
        if not workflow.validation:
            return

        # Check required fields
        if workflow.validation.required_fields:
            result = self.input_validator.validate_required_fields(
                extracted_data, workflow.validation.required_fields
            )
            if not result.valid:
                raise ValueError(result.error)

        # Validate ICD-10 format if required
        if workflow.validation.icd10_format:
            for key, value in extracted_data.items():
                if 'icd10' in key.lower() and 'code' in key.lower() and value:
                    result = self.icd10_validator.validate_format(str(value))
                    if not result.valid:
                        raise ValueError(result.error)

        # Validate field whitelist
        if workflow.security and workflow.security.allowed_fields:
            whitelist_validator = FieldWhitelistValidator(workflow.security.allowed_fields)
            for output_config in workflow.output:
                result = whitelist_validator.validate(output_config.target_field)
                if not result.valid:
                    raise ValueError(result.error)

    def _log_error(
        self,
        workflow: WorkflowConfig,
        context: Context,
        error_code: str,
        execution_time: int
    ):
        """Log execution error"""
        self.audit_logger.log_workflow_execution(
            workflow_id=workflow.workflow_id,
            connector=workflow.connector,
            status="error",
            execution_time_ms=execution_time,
            user_id=context.user_id,
            error_code=error_code
        )


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing workflow engine...")
    print("=" * 60)

    # This would require full setup with connectors, so just verify import
    print("✅ Workflow engine module loaded successfully")
    print("   Run full integration test with middleware/main.py")
