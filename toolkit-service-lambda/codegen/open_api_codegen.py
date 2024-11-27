import subprocess
import os

from codegen.codegen import Codegen


class OpenApiCodegen(Codegen):
    def generate_project(self, project_id: str, service_info: str):
        service_type = service_info["type"]
        model_location = service_info["openapi"]["model"]

        config = service_info["openapi"].get("config", {})

        app_dir = f"/tmp/{project_id}/app"
        os.makedirs(app_dir, exist_ok=True)

        model_dir = f"/tmp/{project_id}/model"
        os.makedirs(model_dir, exist_ok=True)

        model_filename = os.path.basename(model_location)

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
