"""OpenAPI specification handler for mock server."""

import json
import re
import secrets
from collections.abc import Callable
from datetime import datetime
from typing import Any, cast

import yaml
from jsonschema import ValidationError, validate

# Type aliases
OpenAPIDict = dict[str, Any]

# Constants
APPLICATION_JSON = "application/json"


class OpenAPIHandler:
    """Handler for OpenAPI specification-based mock responses."""

    def __init__(self, spec_path: str) -> None:
        """Initialize with OpenAPI specification file."""
        self.spec_path = spec_path
        self.spec_dict = self._load_spec()
        self._example_generators = self._setup_generators()

    def _load_spec(self) -> OpenAPIDict:
        """Load OpenAPI specification from file."""
        with open(self.spec_path) as f:
            if self.spec_path.endswith(".yaml") or self.spec_path.endswith(".yml"):
                return cast(OpenAPIDict, yaml.safe_load(f))
            return cast(OpenAPIDict, json.load(f))

    def _setup_generators(self) -> dict[str, Callable[[], Any]]:
        """Set up value generators for different formats.

        Uses secrets module for cryptographically secure random generation.
        """
        return {
            "uuid": lambda: str(self._generate_uuid()),
            "date-time": lambda: datetime.now().isoformat(),
            "date": lambda: datetime.now().date().isoformat(),
            "time": lambda: datetime.now().time().isoformat(),
            "email": lambda: f"user{secrets.randbelow(1000) + 1}@example.com",
            "uri": lambda: f"https://example.com/resource/{secrets.randbelow(1000) + 1}",
            "hostname": lambda: f"server{secrets.randbelow(100) + 1}.example.com",
            "ipv4": lambda: f"{secrets.randbelow(255) + 1}.{secrets.randbelow(256)}.{secrets.randbelow(256)}.{secrets.randbelow(255) + 1}",
            # NOSONAR: python:S1313 - Using RFC 5737 documentation IPv6 address
            # 2001:0db8::/32 is reserved for documentation (RFC 3849)
            # This is the official example IP range, not a real production address
            "ipv6": lambda: f"2001:0db8:85a3::{secrets.randbelow(10000):04x}:{secrets.randbelow(10000):04x}",
        }

    def _generate_uuid(self) -> str:
        """Generate a UUID-like string."""
        import uuid

        return str(uuid.uuid4())

    def find_operation(self, method: str, path: str) -> OpenAPIDict | None:
        """Find operation definition for given method and path."""
        # Normalize method to lowercase
        method = method.lower()

        # Try exact match first
        if path in self.spec_dict["paths"]:
            path_item = self.spec_dict["paths"][path]
            if method in path_item:
                return cast(OpenAPIDict, path_item[method])

        # Try pattern matching for path parameters
        for spec_path, path_item in self.spec_dict["paths"].items():
            if method in path_item:
                # Convert OpenAPI path to regex
                pattern = spec_path
                pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
                pattern = f"^{pattern}$"

                if re.match(pattern, path):
                    return cast(OpenAPIDict, path_item[method])

        return None

    def generate_response(
        self, operation: OpenAPIDict, status_code: int = 200
    ) -> OpenAPIDict:
        """Generate response based on OpenAPI schema."""
        responses = operation.get("responses", {})
        response_spec = responses.get(str(status_code))

        if not response_spec:
            # Try to find a default response
            response_spec = responses.get("default")
            if not response_spec:
                return {"message": "No response schema defined"}

        # Get content schema
        content = response_spec.get("content", {})
        json_content = content.get(APPLICATION_JSON, {})
        schema = json_content.get("schema", {})

        if not schema:
            return {"message": response_spec.get("description", "OK")}

        # Resolve schema reference if needed
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        # Generate response based on schema
        return cast(OpenAPIDict, self._generate_from_schema(schema))

    def _resolve_ref(self, ref: str) -> OpenAPIDict:
        """Resolve a JSON reference."""
        # Remove the '#/' prefix
        ref_path = ref.replace("#/", "").split("/")

        result = self.spec_dict
        for part in ref_path:
            result = result.get(part, {})

        return result

    def _handle_schema_composition(self, schema: OpenAPIDict) -> Any | None:
        """Handle allOf, oneOf, anyOf schema composition."""
        if "allOf" in schema:
            result = {}
            for sub_schema in schema["allOf"]:
                sub_result = self._generate_from_schema(sub_schema)
                if isinstance(sub_result, dict):
                    result.update(sub_result)
            return result

        if "oneOf" in schema or "anyOf" in schema:
            schemas = schema.get("oneOf", schema.get("anyOf", []))
            if schemas:
                return self._generate_from_schema(schemas[0])

        return None

    def _get_example_value(self, schema: OpenAPIDict) -> Any | None:
        """Get example value from schema if available."""
        if "example" in schema:
            return schema["example"]

        if "examples" in schema and isinstance(schema["examples"], list):
            examples = schema["examples"]
            return examples[secrets.randbelow(len(examples))]

        return None

    def _generate_by_type(self, schema: OpenAPIDict, schema_type: str) -> Any:
        """Generate value based on schema type."""
        type_generators = {
            "object": self._generate_object,
            "array": self._generate_array,
            "string": self._generate_string,
            "number": self._generate_number,
            "integer": self._generate_number,
            # Uses secrets for cryptographically secure random generation
            "boolean": lambda _: bool(secrets.randbelow(2)),
            "null": lambda _: None,
        }

        generator = type_generators.get(schema_type)
        if generator:
            return generator(schema)
        return None

    def _generate_from_schema(self, schema: OpenAPIDict) -> Any:
        """Generate data based on JSON schema."""
        # Handle references
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        # Try schema composition (allOf, oneOf, anyOf)
        composition_result = self._handle_schema_composition(schema)
        if composition_result is not None:
            return composition_result

        # Try to get example value
        example_value = self._get_example_value(schema)
        if example_value is not None:
            return example_value

        # Generate by type
        schema_type = schema.get("type", "object")
        return self._generate_by_type(schema, schema_type)

    def _generate_object(self, schema: OpenAPIDict) -> OpenAPIDict:
        """Generate object based on schema."""
        result = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            # Always include required properties
            if (
                prop_name in required or secrets.randbelow(100) > 30
            ):  # 70% chance for optional
                result[prop_name] = self._generate_from_schema(prop_schema)

        return result

    def _generate_array(self, schema: OpenAPIDict) -> list[Any]:
        """Generate array based on schema."""
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 0)
        max_items = schema.get("maxItems", 5)

        # Generate random number of items
        num_items = secrets.randbelow(max_items - min_items + 1) + min_items

        return [self._generate_from_schema(items_schema) for _ in range(num_items)]

    def _generate_string(self, schema: OpenAPIDict) -> str:
        """Generate string based on schema."""
        # Check for enum
        if "enum" in schema:
            enum_values = schema["enum"]
            return str(enum_values[secrets.randbelow(len(enum_values))])

        # Check for format
        format_type = schema.get("format")
        if format_type and format_type in self._example_generators:
            return str(self._example_generators[format_type]())

        # Check for pattern
        pattern = schema.get("pattern")
        if pattern:
            # Simple pattern handling (not full regex generation)
            if pattern == "^[0-9]+$":
                return str(secrets.randbelow(90000) + 10000)
            if pattern == "^[A-Z]{3}$":
                chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                return "".join(chars[secrets.randbelow(len(chars))] for _ in range(3))
            if pattern == r"^\d{4}-\d{2}$":
                year = secrets.randbelow(6) + 2020
                month = secrets.randbelow(12) + 1
                return f"{year}-{month:02d}"

        # Default string generation
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", 20)
        length = secrets.randbelow(max_length - min_length + 1) + min_length

        suffix = secrets.randbelow(1000) + 1
        return f"string_{suffix}"[:length]

    def _generate_number(self, schema: OpenAPIDict) -> int | float:
        """Generate number based on schema."""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)

        if schema.get("type") == "integer":
            return secrets.randbelow(int(maximum) - int(minimum) + 1) + int(minimum)
        # For float, use secrets to generate a fraction
        int_part = secrets.randbelow(int(maximum) - int(minimum) + 1) + int(minimum)
        frac_part = secrets.randbelow(100) / 100.0
        return round(int_part + frac_part, 2)

    def _validate_request_body(self, operation: OpenAPIDict, body: dict) -> str | None:
        """Validate request body against schema."""
        request_body_spec = operation["requestBody"]
        if not request_body_spec.get("required", False) and not body:
            return None

        content = request_body_spec.get("content", {})
        json_content = content.get(APPLICATION_JSON, {})
        schema = json_content.get("schema", {})

        if not schema:
            return None

        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        try:
            validate(body, schema)
        except ValidationError as e:
            return f"Request body validation error: {e.message}"

        return None

    def _validate_query_parameter(
        self, param_spec: OpenAPIDict, query_params: dict
    ) -> str | None:
        """Validate a single query parameter."""
        param_name = param_spec["name"]
        required = param_spec.get("required", False)

        if required and param_name not in query_params:
            return f"Missing required query parameter: {param_name}"

        if param_name not in query_params:
            return None

        # Validate parameter schema
        param_schema = param_spec.get("schema", {})
        try:
            validate(query_params[param_name], param_schema)
        except ValidationError as e:
            return f"Query parameter '{param_name}' validation error: {e.message}"

        return None

    def _validate_query_parameters(
        self, operation: OpenAPIDict, query_params: dict
    ) -> str | None:
        """Validate all query parameters."""
        parameters = operation.get("parameters", [])

        for param_spec in parameters:
            if param_spec.get("in") != "query":
                continue

            error = self._validate_query_parameter(param_spec, query_params)
            if error:
                return error

        return None

    def validate_request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        query_params: dict | None = None,
    ) -> str | None:
        """Validate request against OpenAPI schema."""
        operation = self.find_operation(method, path)
        if not operation:
            return f"No operation found for {method} {path}"

        # Validate request body if present
        if body and "requestBody" in operation:
            error = self._validate_request_body(operation, body)
            if error:
                return error

        # Validate query parameters
        if query_params:
            error = self._validate_query_parameters(operation, query_params)
            if error:
                return error

        return None  # Validation passed

    def get_operation_examples(self, method: str, path: str) -> OpenAPIDict:
        """Get all examples for an operation."""
        operation = self.find_operation(method, path)
        if not operation:
            return {}

        examples: OpenAPIDict = {"request": {}, "responses": {}}

        # Extract request examples
        if "requestBody" in operation:
            content = operation["requestBody"].get("content", {})
            json_content = content.get(APPLICATION_JSON, {})
            if "example" in json_content:
                examples["request"]["body"] = json_content["example"]
            elif "examples" in json_content:
                examples["request"]["examples"] = json_content["examples"]

        # Extract response examples
        for status_code, response_spec in operation.get("responses", {}).items():
            content = response_spec.get("content", {})
            json_content = content.get(APPLICATION_JSON, {})
            if "example" in json_content:
                examples["responses"][status_code] = json_content["example"]
            elif "examples" in json_content:
                examples["responses"][f"{status_code}_examples"] = json_content[
                    "examples"
                ]

        return examples


# Global instance
_openapi_handler: OpenAPIHandler | None = None


def setup_openapi_handler(spec_path: str) -> OpenAPIHandler:
    """Set up global OpenAPI handler."""
    global _openapi_handler
    _openapi_handler = OpenAPIHandler(spec_path)
    return _openapi_handler


def get_openapi_handler() -> OpenAPIHandler | None:
    """Get global OpenAPI handler instance."""
    return _openapi_handler
