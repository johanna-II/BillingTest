"""Swagger UI integration for mock server."""

from pathlib import Path

import yaml  # type: ignore[import-untyped]
from flask import Blueprint, render_template_string

swagger_bp = Blueprint("swagger", __name__)

# Constants
OPENAPI_SPEC_FILE = "billing-api.yaml"
OPENAPI_SPEC_NOT_FOUND = "OpenAPI specification not found"


SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Billing API - Swagger UI</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui.css" />
    <style>
        body {
            margin: 0;
            padding: 0;
        }
        .swagger-ui .topbar {
            display: none;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.5.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const spec = {{ spec|tojson }};

            // Update server URL to current host
            if (spec.servers && spec.servers.length > 0) {
                spec.servers[0].url = window.location.origin + '/api/v1';
            }

            window.ui = SwaggerUIBundle({
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                validatorUrl: null
            });
        };
    </script>
</body>
</html>
"""


@swagger_bp.route("/")
@swagger_bp.route("/index.html")
def swagger_ui():
    """Serve Swagger UI."""
    # Load OpenAPI spec
    spec_path = Path(__file__).parent.parent / "docs" / "openapi" / OPENAPI_SPEC_FILE

    if not spec_path.exists():
        return OPENAPI_SPEC_NOT_FOUND, 404

    # Load and parse YAML
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    # Render template with spec
    return render_template_string(SWAGGER_UI_TEMPLATE, spec=spec)


@swagger_bp.route("/openapi.json")
def openapi_json():
    """Serve OpenAPI spec as JSON."""
    spec_path = Path(__file__).parent.parent / "docs" / "openapi" / OPENAPI_SPEC_FILE

    if not spec_path.exists():
        return {"error": OPENAPI_SPEC_NOT_FOUND}, 404

    with open(spec_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@swagger_bp.route("/openapi.yaml")
def openapi_yaml():
    """Serve OpenAPI spec as YAML."""
    spec_path = Path(__file__).parent.parent / "docs" / "openapi" / OPENAPI_SPEC_FILE

    if not spec_path.exists():
        return OPENAPI_SPEC_NOT_FOUND, 404

    with open(spec_path, encoding="utf-8") as f:
        content = f.read()

    from flask import Response

    return Response(content, mimetype="application/x-yaml")
