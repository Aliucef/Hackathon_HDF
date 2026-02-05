"""
Transformers
Template rendering and response extraction
"""

from jinja2 import Template, TemplateSyntaxError, UndefinedError
from jsonpath_ng import parse as jsonpath_parse
from typing import Dict, Any, Optional
import json


class TemplateRenderer:
    """Renders Jinja2 templates"""

    def render(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template with given context

        Args:
            template_str: Template string with Jinja2 syntax
            context: Dictionary of variables to inject

        Returns:
            Rendered string

        Raises:
            TemplateSyntaxError: If template syntax is invalid
            UndefinedError: If required variable is missing
        """
        try:
            template = Template(template_str)
            rendered = template.render(**context)
            return rendered
        except TemplateSyntaxError as e:
            raise ValueError(f"Template syntax error: {e}")
        except UndefinedError as e:
            raise ValueError(f"Missing template variable: {e}")

    def render_json(self, template_str: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render a template and parse as JSON

        Args:
            template_str: Template string that should produce JSON
            context: Dictionary of variables to inject

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If result is not valid JSON
        """
        rendered = self.render(template_str, context)

        try:
            return json.loads(rendered)
        except json.JSONDecodeError as e:
            raise ValueError(f"Rendered template is not valid JSON: {e}\nRendered: {rendered}")


class ResponseExtractor:
    """Extracts data from API responses using JSONPath"""

    def extract(self, response_data: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Extract fields from response using JSONPath expressions

        Args:
            response_data: API response dictionary
            mappings: Dictionary of {output_name: jsonpath_expression}

        Returns:
            Dictionary of extracted values

        Example:
            mappings = {
                'summary': '$.summary',
                'icd10_code': '$.icd10.code',
                'confidence': '$.confidence'
            }
            response = {
                'summary': 'Pneumonia',
                'icd10': {'code': 'J18.9', 'label': 'Pneumonia'},
                'confidence': 0.95
            }
            result = extractor.extract(response, mappings)
            # Returns: {'summary': 'Pneumonia', 'icd10_code': 'J18.9', 'confidence': 0.95}
        """
        extracted = {}

        for output_name, jsonpath_expr in mappings.items():
            try:
                # Parse JSONPath expression
                jsonpath = jsonpath_parse(jsonpath_expr)

                # Find matches
                matches = jsonpath.find(response_data)

                if not matches:
                    # Field not found
                    extracted[output_name] = None
                elif len(matches) == 1:
                    # Single value
                    extracted[output_name] = matches[0].value
                else:
                    # Multiple values - return as list
                    extracted[output_name] = [match.value for match in matches]

            except Exception as e:
                raise ValueError(f"Error extracting '{output_name}' with path '{jsonpath_expr}': {e}")

        return extracted

    def extract_single(
        self,
        response_data: Dict[str, Any],
        jsonpath_expr: str,
        default: Any = None
    ) -> Any:
        """
        Extract a single value from response

        Args:
            response_data: API response dictionary
            jsonpath_expr: JSONPath expression
            default: Default value if not found

        Returns:
            Extracted value or default
        """
        try:
            jsonpath = jsonpath_parse(jsonpath_expr)
            matches = jsonpath.find(response_data)

            if matches:
                return matches[0].value
            return default

        except Exception:
            return default


class OutputBuilder:
    """Builds output instructions from templates and extracted data"""

    def __init__(self):
        self.renderer = TemplateRenderer()

    def build_instructions(
        self,
        output_configs: list,
        extracted_data: Dict[str, Any]
    ) -> list:
        """
        Build insertion instructions from output configs and extracted data

        Args:
            output_configs: List of OutputConfig dictionaries
            extracted_data: Extracted data from response

        Returns:
            List of InsertionInstruction dictionaries
        """
        from .models import InsertionInstruction

        instructions = []

        for config in output_configs:
            try:
                # Render content template
                content = self.renderer.render(config.content, extracted_data)

                # Render label if present (for ICD-10)
                label = None
                if config.label:
                    label = self.renderer.render(config.label, extracted_data)

                # Create instruction
                instruction = InsertionInstruction(
                    target_field=config.target_field,
                    content=content,
                    mode=config.mode,
                    type=config.type,
                    navigation=config.navigation,
                    label=label
                )

                instructions.append(instruction)

            except Exception as e:
                raise ValueError(f"Error building instruction for field '{config.target_field}': {e}")

        return instructions


# ============================================================================
# Convenience functions
# ============================================================================

def render_template(template_str: str, context: Dict[str, Any]) -> str:
    """Quick template rendering"""
    renderer = TemplateRenderer()
    return renderer.render(template_str, context)


def extract_response(response: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
    """Quick response extraction"""
    extractor = ResponseExtractor()
    return extractor.extract(response, mappings)


# ============================================================================
# Test code
# ============================================================================

if __name__ == "__main__":
    print("Testing transformers...")
    print("=" * 60)

    # Test template rendering
    print("\n1. Template Rendering:")

    renderer = TemplateRenderer()

    template1 = "Hello, {{ name }}!"
    context1 = {"name": "Dr. Smith"}
    result1 = renderer.render(template1, context1)
    print(f"  ✅ Simple: '{result1}'")

    template2 = "Patient diagnosed with {{ diagnosis }}, code: {{ icd10 }}"
    context2 = {"diagnosis": "Pneumonia", "icd10": "J18.9"}
    result2 = renderer.render(template2, context2)
    print(f"  ✅ Medical: '{result2}'")

    # Test JSON rendering
    template_json = '{"text": "{{ input_text }}", "language": "en"}'
    context_json = {"input_text": "Patient presents with cough"}
    result_json = renderer.render_json(template_json, context_json)
    print(f"  ✅ JSON: {result_json}")

    # Test response extraction
    print("\n2. Response Extraction:")

    extractor = ResponseExtractor()

    response = {
        "summary": "Pneumonia with respiratory symptoms",
        "icd10": {
            "code": "J18.9",
            "label": "Pneumonia, unspecified"
        },
        "confidence": 0.92,
        "metadata": {
            "processing_time": 234
        }
    }

    mappings = {
        "summary": "$.summary",
        "icd10_code": "$.icd10.code",
        "icd10_label": "$.icd10.label",
        "confidence": "$.confidence",
        "processing_time": "$.metadata.processing_time"
    }

    extracted = extractor.extract(response, mappings)
    print(f"  ✅ Extracted fields:")
    for key, value in extracted.items():
        print(f"      {key}: {value}")

    # Test output building
    print("\n3. Output Building:")

    from types import SimpleNamespace

    output_builder = OutputBuilder()

    # Mock output configs
    output_configs = [
        SimpleNamespace(
            type="text",
            target_field="DiagnosisText",
            content="{{ summary }}",
            mode="replace",
            navigation=None,
            label=None
        ),
        SimpleNamespace(
            type="icd10",
            target_field="DiagnosisCode",
            content="{{ icd10_code }}",
            mode="replace",
            navigation="tab_3",
            label="{{ icd10_label }}"
        )
    ]

    instructions = output_builder.build_instructions(output_configs, extracted)
    print(f"  ✅ Built {len(instructions)} instructions:")
    for inst in instructions:
        print(f"      {inst.target_field} = '{inst.content}' ({inst.mode})")

    print("\n✅ Transformer tests complete!")
