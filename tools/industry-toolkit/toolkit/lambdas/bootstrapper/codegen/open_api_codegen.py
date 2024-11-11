import subprocess
import os
from codegen.codegen import Codegen

class OpenApiCodegen(Codegen):
    def generate_project(self, project_id: str, event: dict):
        service_type = event.get("serviceType")
        model_url = event.get("model")
        config = event.get("config", {})
        app_dir = f"/tmp/{project_id}/app"

        os.makedirs(app_dir, exist_ok=True)

        command = [
            "java",
            "-jar",
            "/opt/openapi-generator-cli.jar",
            "generate",
            "-i", model_url,
            "-g", service_type,
            "-o", app_dir,
            "--additional-properties", ",".join(f"{k}={v}" for k, v in config.items())
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Project generated successfully at {app_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate project: {e}")
            raise RuntimeError(f"Error running OpenAPI Generator: {e}")