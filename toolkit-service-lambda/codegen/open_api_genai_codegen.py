import subprocess
import boto3
import json
import os

from codegen.codegen import Codegen

# "service": {
#   "type": "spring",
#   "name": "my-service-01",
#   "description": "My new service",
#   "openapi-gen": {
#     "prompt": "Create me a shopping cart service with OpenAPI that has operation to create, read, update, and delete carts, and to add and remove CartItems to a cart. Model objects should end in Request or Response.",
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


class OpenApiGenAiCodegen(Codegen):
    def generate_project(self, project_id: str, service_info: str):
        service_type = service_info["type"]

        config = service_info["openapi-gen"].get("config", {})

        app_dir = f"/tmp/{project_id}/app"
        os.makedirs(app_dir, exist_ok=True)

        model_dir = f"/tmp/{project_id}/model"
        os.makedirs(model_dir, exist_ok=True)

        model_filename = service_info["name"] + ".yaml"
        model_local_path = os.path.join(model_dir, model_filename)

        prompt = service_info["openapi-gen"]["prompt"]

        self.generate_model_with_bedrock(prompt, model_local_path)

        command = [
            "java",
            "-jar",
            "/opt/openapi-generator-cli.jar",
            "generate",
            "-i", model_local_path,
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

    def generate_model_with_bedrock(self, prompt: str, output_path: str):
        client = boto3.client("bedrock-runtime")

        additional_prompt = "The service should be defined in OpenAPI using YAML format."
        formatted_prompt = f"Human: {prompt} {additional_prompt}\nAssistant:"

        response = client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                "messages": [
                    {"role": "user", "content": formatted_prompt}
                ],
                "max_tokens": 10000,
                "anthropic_version": "bedrock-2023-05-31"
            })
        )

        model_response = json.loads(response["body"].read())
        print(model_response)
        response_text = model_response["content"][0]["text"]

        split_text = response_text.split('```yaml', 1)

        if len(split_text) > 1:
            generated_content = split_text[1].split('```', 1)[0].strip()
        else:
            generated_content = ""

        with open(output_path, "w") as model_file:
            model_file.write(generated_content)
        print(f"Generated model saved to {output_path}")
        print(generated_content)