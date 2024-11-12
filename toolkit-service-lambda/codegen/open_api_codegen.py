import subprocess
import os

from codegen.codegen import Codegen

# "service": {
#   "type": "spring",
#   "name": "my-service",
#   "description": "My new service",
#   "openapi": {
#     "model": "https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/product-catalog/model/product-catalog.openapi.yaml",
#     "config": {
#       "basePackage": "com.amazonaws.example",
#       "modelPackage": "com.amazonaws.example.model",
#       "apiPackage": "com.amazonaws.example.api",
#       "invokerPackage": "com.amazonaws.example.configuration",
#       "groupId": "com.amazonaws.example",
#       "artifactId": "cz-order-service"
#     }
#   }
# }


class OpenApiCodegen(Codegen):
    def generate_project(self, project_id: str, service_info: str):
        service_type = service_info["type"]
        model_location = service_info["openapi"]["model"]

        config = service_info["openapi"].get("config", {})

        app_dir = f"/tmp/{project_id}/app"
        os.makedirs(app_dir, exist_ok=True)

        command = [
            "java",
            "-jar",
            "/opt/openapi-generator-cli.jar",
            "generate",
            "-i", model_location,
            "-g", service_type,
            "-o", app_dir,
            "--additional-properties", ",".join(f"{k}={v}" for k, v in config.items())
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Project generated successfully at {app_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate project: {e}")
            raise RuntimeError(f"Error running OpenAPI Generator: {e.stderr}")
