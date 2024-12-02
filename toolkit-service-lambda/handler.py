import boto3
import json
import uuid
import os
from datetime import datetime
from aws_lambda_powertools.logging import Logger

from codebuild.java_maven_buildspec_generator import JavaMavenBuildspecGenerator
from codegen.open_api_codegen import OpenApiCodegen
from codegen.open_api_genai_codegen import OpenApiGenAiCodegen
from codegen.open_api_genai_codegen_v2 import OpenApiGenAiCodegenV2
from docker.java_spring_boot_generator import JavaSpringBootDockerfileGenerator
from docker_registry.ecr_registry import EcrRegistry
from infra.cloudformation_infra_generator import CloudFormationInfraGenerator
from pipeline.aws_code_pipeline import AwsCodePipeline
from source_repo.github_source_repo import GitHubSourceRepo

logger = Logger()

dynamodb = boto3.resource("dynamodb")
services_table_name = os.getenv("SERVICES_TABLE_NAME", "ServicesTable")
services_table = dynamodb.Table(services_table_name)


def process_service_creation(payload):
    """Processes the input payload to create a new service."""
    logger.info(f"Received input payload: {payload}")

    service_info = payload["service"]
    service_type = service_info["type"]
    scm_type, scm_info = next(iter(payload.get("scm", {}).items()), (None, {}))
    iac_type, iac_info = next(iter(payload.get("iac", {}).items()), (None, {}))

    project_id = str(uuid.uuid4())
    logger.info(f"Creating project with id {project_id}...")

    project_dir = f"/tmp/{project_id}"
    app_dir = f"{project_dir}/app"
    os.makedirs(app_dir, exist_ok=True)

    # Generate project source code
    logger.info(f"Creating project type '{service_type}'...")

    if "openapi" in service_info:
        codegen = OpenApiCodegen()
    elif "openapi-gen" in service_info:
        codegen = OpenApiGenAiCodegen()
    elif "openapi-gen-v2" in service_info:
        codegen = OpenApiGenAiCodegenV2()
    else:
        raise ValueError(f"Unsupported model type.")

    codegen.generate_project(project_id, service_info)

    # Create Dockerfile
    logger.info(f"Creating Dockerfile for project type {service_type}...")

    if service_type == "spring":
        generator = JavaSpringBootDockerfileGenerator()
        generator.generate_dockerfile(project_id)
    else:
        raise ValueError(f"Unsupported project type: {service_type}")

    # Create container registry
    registry_name = service_info["name"]
    logger.info(f"Creating ECR Registry named {registry_name}...")

    registry = EcrRegistry()
    registry.create_repository(registry_name)

    # Generate IaC code
    logger.info(f"Creating IaC code for {iac_type}...")

    if iac_type == "cloudformation":
        infra_generator = CloudFormationInfraGenerator()
        infra_generator.generate_infra(project_id, iac_info)
    else:
        raise ValueError(f"Unsupported iac_type type: {iac_type}")

    # Create AWS CodeBuild buildspec file
    buildspec = JavaMavenBuildspecGenerator()
    buildspec.generate_buildspec(project_id, service_info)

    # Create SCM repo
    logger.info(f"Creating SCM repo type '{scm_type}'...")

    if scm_type == "github":
        repo = GitHubSourceRepo(scm_info)
        repo.create_repo()
        repo.commit(project_dir, "Initial commit")
    else:
        raise ValueError(f"Unsupported scm_type type: {scm_type}")

    # Create AWS CodePipeline
    aws_pipeline = AwsCodePipeline()
    aws_pipeline.create_pipeline(service_info, scm_info)

    # Write record to DynamoDB
    timestamp = datetime.utcnow().isoformat()
    item = {
        "id": project_id,
        "project_name": service_info["name"],
        "project_type": service_type,
        "description": service_info["description"],
        "github_repo": scm_info["repo"],
        "created_timestamp": timestamp,
        "updated_timestamp": timestamp,
        "metadata": {},
    }

    try:
        services_table.put_item(Item=item)
        logger.info(f"Successfully inserted project {project_id} into DynamoDB: {item}")
    except Exception as e:
        logger.error(f"Failed to insert item: {e}")

    logger.info(f"Successfully inserted project {project_id} into DynamoDB")

    return item


@logger.inject_lambda_context
def lambda_handler(event, context):
    """
    AWS Lambda Handler.
    Expects `event` to contain the payload with service information.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        result = process_service_creation(event)

        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }

    except Exception as e:
        logger.error(f"Error processing service creation: {e}")
        logger.error("Traceback:", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "An error occurred while processing the service creation."}),
        }


def main():
    """Main function for local testing."""
    event = {
        "service": {
            "name": "MyService",
            "type": "spring",
            "description": "A sample service",
            "openapi-gen-v2": {
                "prompt": "Create an API for a shopping cart.",
                "config": {
                    "basePackage": "com.example",
                    "modelPackage": "com.example.model",
                    "apiPackage": "com.example.api",
                    "invokerPackage": "com.example.invoker",
                    "groupId": "com.example",
                    "artifactId": "shopping-cart-service"
                }
            }
        },
        "scm": {
            "github": {
                "repo": "https://github.com/example/shopping-cart-service",
                "token": "my-github-token"
            }
        },
        "iac": {
            "cloudformation": {}
        }
    }

    result = process_service_creation(event)
    print("Result:", json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
