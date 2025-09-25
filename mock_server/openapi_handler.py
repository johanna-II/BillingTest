"""OpenAPI specification handler for mock server."""

import json
import random
import re
from datetime import datetime
from typing import Any

import yaml
from jsonschema import ValidationError, validate


class OpenAPIHandler:
    """Handler for OpenAPI specification-based mock responses."""

    def __init__(self, spec_path: str) -> None:
        """Initialize with OpenAPI specification file."""
        self.spec_path = spec_path
        self.spec_dict = self._load_spec()
        self._example_generators = self._setup_generators()

    def _load_spec(self) -> dict:
        """Load OpenAPI specification from file."""
        with open(self.spec_path) as f:
            if self.spec_path.endswith(".yaml") or self.spec_path.endswith(".yml"):
                return yaml.safe_load(f)
            return json.load(f)

    def _setup_generators(self) -> dict[str, callable]:
        """Set up value generators for different formats."""
        return {
            "uuid": lambda: str(self._generate_uuid()),
            "date-time": lambda: datetime.now().isoformat(),
            "date": lambda: datetime.now().date().isoformat(),
            "time": lambda: datetime.now().time().isoformat(),
            "email": lambda: f"user{random.randint(1, 1000)}@example.com",
            "uri": lambda: f"https://example.com/resource/{random.randint(1, 1000)}",
            "hostname": lambda: f"server{random.randint(1, 100)}.example.com",
            "ipv4": lambda: f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}",
            "ipv6": lambda: "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        }

    def _generate_uuid(self) -> str:
        """Generate a UUID-like string."""
        import uuid

        return str(uuid.uuid4())

    def find_operation(self, method: str, path: str) -> dict[str, Any] | None:
        """Find operation definition for given method and path."""
        # Normalize method to lowercase
        method = method.lower()

        # Try exact match first
        if path in self.spec_dict["paths"]:
            path_item = self.spec_dict["paths"][path]
            if method in path_item:
                return path_item[method]

        # Try pattern matching for path parameters
        for spec_path, path_item in self.spec_dict["paths"].items():
            if method in path_item:
                # Convert OpenAPI path to regex
                pattern = spec_path
                pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
                pattern = f"^{pattern}$"

                if re.match(pattern, path):
                    return path_item[method]

        return None

    def generate_response(
        self, operation: dict[str, Any], status_code: int = 200
    ) -> dict[str, Any]:
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
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})

        if not schema:
            return {"message": response_spec.get("description", "OK")}

        # Resolve schema reference if needed
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        # Generate response based on schema
        return self._generate_from_schema(schema)

    def _resolve_ref(self, ref: str) -> dict[str, Any]:
        """Resolve a JSON reference."""
        # Remove the '#/' prefix
        ref_path = ref.replace("#/", "").split("/")

        result = self.spec_dict
        for part in ref_path:
            result = result.get(part, {})

        return result

    def _generate_from_schema(self, schema: dict[str, Any]) -> Any:
        """Generate data based on JSON schema."""
        # Handle references
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        # Handle allOf, oneOf, anyOf
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
                # Pick first schema for simplicity
                return self._generate_from_schema(schemas[0])

        # Handle examples
        if "example" in schema:
            return schema["example"]

        if "examples" in schema and isinstance(schema["examples"], list):
            return random.choice(schema["examples"])

        # Handle different types
        schema_type = schema.get("type", "object")

        if schema_type == "object":
            return self._generate_object(schema)
        if schema_type == "array":
            return self._generate_array(schema)
        if schema_type == "string":
            return self._generate_string(schema)
        if schema_type in {"number", "integer"}:
            return self._generate_number(schema)
        if schema_type == "boolean":
            return random.choice([True, False])
        if schema_type == "null":
            return None

        return None

    def _generate_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate object based on schema."""
        result = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            # Always include required properties
            if (
                prop_name in required or random.random() > 0.3
            ):  # 70% chance for optional
                result[prop_name] = self._generate_from_schema(prop_schema)

        return result

    def _generate_array(self, schema: dict[str, Any]) -> list[Any]:
        """Generate array based on schema."""
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 0)
        max_items = schema.get("maxItems", 5)

        # Generate random number of items
        num_items = random.randint(min_items, max_items)

        return [self._generate_from_schema(items_schema) for _ in range(num_items)]

    def _generate_string(self, schema: dict[str, Any]) -> str:
        """Generate string based on schema."""
        # Check for enum
        if "enum" in schema:
            return random.choice(schema["enum"])

        # Check for format
        format_type = schema.get("format")
        if format_type and format_type in self._example_generators:
            return self._example_generators[format_type]()

        # Check for pattern
        pattern = schema.get("pattern")
        if pattern:
            # Simple pattern handling (not full regex generation)
            if pattern == "^[0-9]+$":
                return str(random.randint(10000, 99999))
            if pattern == "^[A-Z]{3}$":
                return "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
            if pattern == r"^\d{4}-\d{2}$":
                return f"{random.randint(2020, 2025)}-{random.randint(1, 12):02d}"

        # Default string generation
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", 20)
        length = random.randint(min_length, max_length)

        return f"string_{random.randint(1, 1000)}"[:length]

    def _generate_number(self, schema: dict[str, Any]) -> int | float:
        """Generate number based on schema."""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)

        if schema.get("type") == "integer":
            return random.randint(int(minimum), int(maximum))
        return round(random.uniform(minimum, maximum), 2)

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
            request_body_spec = operation["requestBody"]
            if request_body_spec.get("required", False) or body:
                content = request_body_spec.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema", {})

                if schema:
                    if "$ref" in schema:
                        schema = self._resolve_ref(schema["$ref"])

                    try:
                        validate(body, schema)
                    except ValidationError as e:
                        return f"Request body validation error: {e.message}"

        # Validate query parameters
        if query_params and "parameters" in operation:
            for param_spec in operation["parameters"]:
                if param_spec["in"] == "query":
                    param_name = param_spec["name"]
                    required = param_spec.get("required", False)

                    if required and param_name not in query_params:
                        return f"Missing required query parameter: {param_name}"

                    if param_name in query_params:
                        # Validate parameter schema
                        param_schema = param_spec.get("schema", {})
                        try:
                            validate(query_params[param_name], param_schema)
                        except ValidationError as e:
                            return f"Query parameter '{param_name}' validation error: {e.message}"

        return None  # Validation passed

    def get_operation_examples(self, method: str, path: str) -> dict[str, Any]:
        """Get all examples for an operation."""
        operation = self.find_operation(method, path)
        if not operation:
            return {}

        examples = {"request": {}, "responses": {}}

        # Extract request examples
        if "requestBody" in operation:
            content = operation["requestBody"].get("content", {})
            json_content = content.get("application/json", {})
            if "example" in json_content:
                examples["request"]["body"] = json_content["example"]
            elif "examples" in json_content:
                examples["request"]["examples"] = json_content["examples"]

        # Extract response examples
        for status_code, response_spec in operation.get("responses", {}).items():
            content = response_spec.get("content", {})
            json_content = content.get("application/json", {})
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
