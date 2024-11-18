import boto3
import json
import uuid
import os

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import Logger
from datetime import datetime

from codebuild.java_maven_buildspec_generator import JavaMavenBuildspecGenerator
from codegen.open_api_codegen import OpenApiCodegen
from codegen.open_api_genai_codegen import OpenApiGenAiCodegen
from docker.java_spring_boot_generator import JavaSpringBootDockerfileGenerator
from docker_registry.ecr_registry import EcrRegistry
from infra.cloudformation_infra_generator import CloudFormationInfraGenerator
from pipeline.aws_code_pipeline import AwsCodePipeline
from source_repo.github_source_repo import GitHubSourceRepo

logger = Logger()
app = APIGatewayRestResolver()
dynamodb = boto3.resource('dynamodb')
services_table_name = os.getenv("SERVICES_TABLE_NAME")
services_table = dynamodb.Table(services_table_name)


@app.post("/services")
def post_services():
    body = app.current_event.json_body
    logger.info(f"Received POST request body: {body}")

    service_info = body["service"]
    service_type = service_info["type"]
    scm_type, scm_info = next(iter(body.get("scm", {}).items()), (None, {}))
    iac_type, iac_info = next(iter(body.get("iac", {}).items()), (None, {}))

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
    else:
        raise ValueError(f"Unsupported model type.")

    codegen.generate_project(project_id, service_info)

    # Create Dockerfile
    logger.info(f"Creating Dockerfile for project type {service_type}...")

    project_type = service_info["type"]

    if service_type == 'spring':
        generator = JavaSpringBootDockerfileGenerator()
        generator.generate_dockerfile(project_id)
    else:
        raise ValueError(f"Unsupported project type: {project_type}")

    # Create container docker_registry
    registry_name = service_info["name"]
    logger.info(f"Creating ECR Registry named {registry_name}")

    registry = EcrRegistry()
    registry.create_repository(registry_name)

    # Generate IaC code
    logger.info(f"Creating IaC code for {iac_type}...")

    if iac_type == 'cloudformation':
        infra_generator = CloudFormationInfraGenerator()
        infra_generator.generate_infra(project_id)

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
        "project_name": service_info['name'],
        "project_type": project_type,
        "description": service_info["description"],
        "github_repo": scm_info["repo"],
        "created_timestamp": timestamp,
        "updated_timestamp": timestamp,
        "metadata": {
        }
    }

    try:
        services_table.put_item(Item=item)
        logger.info(f"Successfully inserted project {project_id} into DynamoDB: {item}")
    except Exception as e:
        logger.error(f"Failed to insert item: {e}")

    logger.info(f"Successfully inserted project {project_id} into DynamoDB")

    return item


@app.get("/services/<project_id>")
def get_service(project_id: str):
    try:
        response = services_table.get_item(Key={"id": project_id})
        item = response.get("Item")

        if not item:
            return {"message": f"Service with project_id {project_id} not found"}, 404

        return item, 200
    except Exception as e:
        logger.error(f"Failed to retrieve project {project_id}: {e}")
        return {"message": "An error occurred while retrieving the service"}, 500


@logger.inject_lambda_context
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)


if __name__ == "__main__":
    test_event_post = {
        "httpMethod": "POST",
        "body": json.dumps({
            "service": {
                "type": "spring",
                "name": "my-service",
                "description": "My new service",
                "openapi": {
                    "model": "https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/product-catalog/model/product-catalog.openapi.yaml",
                    "config": {
                        "basePackage": "com.amazonaws.example",
                        "modelPackage": "com.amazonaws.example.model",
                        "apiPackage": "com.amazonaws.example.api",
                        "invokerPackage": "com.amazonaws.example.configuration",
                        "groupId": "com.amazonaws.example",
                        "artifactId": "cz-order-service"
                    }
                }
            },
            "scm": {
                "github": {
                    "repo": "https://github.com/gchagnon/cz-order-service01a",
                    "secretKey": "greg-github",
                    "email": "none@none.com",
                    "name": "Robot"
                }
            },
            "iac": {
                "cloudformation": {}
            }
        }),
        "resource": "/services",
        "path": "/services",
        "isBase64Encoded": False,
        "requestContext": {},
        "headers": {
            "Content-Type": "application/json"
        }
    }

    test_event_get = {
        "httpMethod": "GET",
        "resource": "/services/{project_id}",
        "path": "/services/1234",
        "pathParameters": {
            "project_id": "1234"
        },
        "isBase64Encoded": False,
        "requestContext": {},
        "headers": {
            "Content-Type": "application/json"
        }
    }

    class MockContext():
        def __init__(self):
            self.function_name = "local_lambda_test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:us-west-2:123456789012:function:local_lambda_test"
            self.aws_request_id = str(uuid.uuid4())

    print("Testing POST /services")
    response_post = lambda_handler(test_event_post, MockContext())
    print("POST Response:", response_post)

    # print("\nTesting GET /services/{project_id}")
    # response_get = lambda_handler(test_event_get, MockContext())
    # print("GET Response:", response_get)