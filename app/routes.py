import json
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from app.services.inference_service import InferenceError, run_inference


def register_routes(app: Flask) -> None:
    sample_payload_path = Path(__file__).resolve().parent.parent / "examples" / "input" / "sample_request.json"
    try:
        sample_request_payload = json.loads(sample_payload_path.read_text(encoding="utf-8"))
    except Exception:
        sample_request_payload = {"meta-data": {"dmp_sample_id": "SAMPLE_DEMO_001_IM7"}}

    openapi_spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "OncoInfer API",
            "version": "1.0.0",
            "description": "Inference API for molecular tumor classification.",
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "Service is healthy"}},
                }
            },
            "/classify/{version}": {
                "post": {
                    "summary": "Run tumor classification",
                    "parameters": [
                        {
                            "name": "version",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"},
                                "example": sample_request_payload,
                            },
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "features": {"type": "string", "format": "binary"}
                                    },
                                    "required": ["features"],
                                }
                            },
                        },
                    },
                    "responses": {
                        "200": {"description": "Prediction response"},
                        "400": {"description": "Validation error"},
                        "500": {"description": "Inference error"},
                    },
                }
            },
            "/docs": {
                "get": {
                    "summary": "Simple endpoint list",
                    "responses": {"200": {"description": "Endpoint reference"}},
                }
            },
            "/openapi.json": {
                "get": {
                    "summary": "OpenAPI document",
                    "responses": {"200": {"description": "OpenAPI JSON"}},
                }
            },
            "/openapi": {
                "get": {
                    "summary": "Swagger UI",
                    "responses": {"200": {"description": "Interactive API docs"}},
                }
            },
        },
    }

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/docs")
    def docs():
        return jsonify(
            {
                "service": "OncoInfer",
                "endpoints": [
                    {"method": "GET", "path": "/", "description": "Legacy upload page"},
                    {"method": "GET", "path": "/health", "description": "Service health check"},
                    {"method": "POST", "path": "/classify/<version>", "description": "Run tumor classification"},
                    {"method": "GET", "path": "/docs", "description": "Endpoint reference"},
                    {"method": "GET", "path": "/openapi.json", "description": "OpenAPI schema"},
                    {"method": "GET", "path": "/openapi", "description": "Swagger UI"},
                ],
            }
        )

    @app.get("/openapi.json")
    def openapi_json():
        return jsonify(openapi_spec)

    @app.get("/openapi")
    def openapi_ui():
        return Response(
            """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>OncoInfer API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui'
      });
    </script>
  </body>
</html>
            """,
            mimetype="text/html",
        )

    @app.post("/classify/<version>")
    def classify(version: str):
        try:
            result = run_inference(
                version=version,
                payload=request.get_json(silent=True),
                features_file=request.files.get("features"),
                config=app.config,
            )
            return jsonify(result)
        except InferenceError as exc:
            return jsonify({"error": str(exc)}), exc.status_code
