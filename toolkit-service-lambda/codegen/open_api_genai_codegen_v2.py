import boto3
import os
import json
import subprocess

from codegen.codegen import Codegen


class OpenApiGenAiCodegenV2(Codegen):
    def generate_project(self, project_id: str, service_info: str):
        config = service_info["openapi-gen-v2"].get("config", {})

        app_dir = f"/tmp/{project_id}/app"
        infra_dir = f"/tmp/{project_id}/infra"
        os.makedirs(app_dir, exist_ok=True)

        prompt = service_info["openapi-gen-v2"]["prompt"]

        command = [
            "java",
            "-jar",
            "/opt/openapi-generator-cli.jar",
            "generate",
            "-i", "https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/customer/models/customer.openapi.yaml",
            "-g", "spring",
            "-o", app_dir,
            "--additional-properties", ",".join(f"{k}={v}" for k, v in config.items())
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            print(f"Project generated successfully at {app_dir}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate project: {e}")
            raise RuntimeError(f"Error running OpenAPI Generator: {e.stderr}")

        # Create gradle file
        prompt = """
        Create a gradle file for a java 8 spring boot project. Also include DynamoDB lib from the AWS SDK v2. 
        """
        self.generate_source_file(self, f"{app_dir}/build.gradle", prompt)

        # Create infra.yaml
        prompt = """
        Create a CloudFormation script in yaml. It will create a Fargate task that runs a Java Spring Boot service. It will
        create a DynamoDB table and pass in the name of the table to the Fargate task as an environment variable. It will
        take parameters for the VPC ID, subnets, and the ECR image tag of the image to run.
        """
        self.generate_source_file(self, f"{infra_dir}/infra.yaml", prompt)

        self.implement_interface(self, f"{app_dir}/src/main/java/com/amazonaws/example/api/CustomersApi.java")

        print(f"Project generated successfully at {app_dir}")

    def implement_interface(self, interface_path: str):
        interface_name = os.path.basename(interface_path).replace(".java", "")
        directory = os.path.dirname(interface_path)
        implementation_name = f"{interface_name}Impl.java"
        implementation_path = os.path.join(directory, implementation_name)

        # Read the interface content
        with open(interface_path, "r") as interface_file:
            interface_content = interface_file.read()

        bedrock = boto3.client('bedrock-runtime')

        prompt = f"""
        You are a Java developer. Implement the following Java interface using DynamoDB as a backend.
        The implementation should use DynamoDBMapper for all CRUD operations. The implementation will be in Java 1.8.
        {interface_content}
        """

        formatted_prompt = f'Human: {prompt}\n\nAssistant:'

        messages = [
            {"role": "system", "content": "You are an expert code generator."},
            {"role": "user", "content": prompt}
        ]

        body = json.dumps({
            "messages": messages,
            "max_tokens_to_sample": 1024,
            "temperature": 0.7,
            "top_p": 0.9
        })

        response = bedrock.invoke_model(
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
        response_text = model_response["content"][0]["text"]

        split_text = response_text.split("```", 1)
        if len(split_text) > 1:
            implementation_code = split_text[1].split("```", 1)[0].strip()
        else:
            implementation_code = split_text.strip()

        # Write the generated implementation to the file
        with open(implementation_path, "w") as impl_file:
            impl_file.write(implementation_code)

        print(f"Implementation written to {implementation_path}")

    def generate_source_file(self, prompt: str, file_path: str, model_id: str = "anthropic.claude-3-5"):
        bedrock = boto3.client('bedrock-runtime')

        messages = [
            {"role": "system", "content": "You are an expert code generator."},
            {"role": "user", "content": prompt}
        ]

        formatted_prompt = f'Human: {prompt}\n\nAssistant:'

        body = json.dumps({
            "messages": messages,
            "max_tokens_to_sample": 1024,
            "temperature": 0.7,
            "top_p": 0.9
        })

        response = bedrock.invoke_model(
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
        response_text = model_response["content"][0]["text"]

        split_text = response_text.split('```', 1)

        if len(split_text) > 1:
            generated_content = split_text[1].split('```', 1)[0].strip()
        else:
            generated_content = ""

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            file.write(generated_content)

