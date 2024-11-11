import boto3
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import Logger
from urllib.parse import urlparse
from datetime import datetime
import uuid
import os

from codebuild.java_maven_pipeline_generator import JavaMavenPipelineGenerator
from codegen.open_api_codegen import OpenApiCodegen
from docker.java_spring_boot_generator import JavaSpringBootDockerfileGenerator
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

    project_id = str(uuid.uuid4())
    logger.info(f"Creating project with id {project_id}...")

    project_dir = f"/tmp/{project_id}"
    app_dir = f"{project_dir}/app"
    os.makedirs(app_dir, exist_ok=True)

    project_type = body.get('serviceType')
    project_config = body.get('config', {})
    service_name = body.get('serviceName')
    model_url = body.get('model')
    target_info = body.get('target')

    if project_type == 'spring':
        generator = JavaSpringBootDockerfileGenerator()
        infra_generator = CloudFormationInfraGenerator()
    else:
        raise ValueError(f"Unsupported project type: {project_type}")

    logger.info("Creating repo: %s...", target_info["repo"])
    repo = GitHubSourceRepo(target_info)
    repo.create_repo()

    codegen = OpenApiCodegen()
    codegen.generate_project(project_id, body)
    dockerfile = generator.generate_dockerfile(project_id, project_config)
    pipeline = JavaMavenPipelineGenerator()
    buildspec = pipeline.generate_pipeline(project_id, project_config)
    infra_path = infra_generator.generate_infra(project_id, project_config)
    repo.commit(project_dir, "Initial commit")

    pipeline_name = f"{service_name}-pipeline"
    repository_name = urlparse(target_info["repo"]).path.strip("/")
    branch_name = "main"
    buildspec_location = "buildspec.yaml"

    aws_pipeline = AwsCodePipeline()
    aws_pipeline.create_pipeline(pipeline_name, repository_name, branch_name, buildspec_location)

    timestamp = datetime.utcnow().isoformat()
    item = {
        "id": project_id,
        "project_name": service_name,
        "project_type": project_type,
        "description": body.get("description", ""),
        "github_repo": target_info["repo"],
        "code_pipeline": pipeline_name,
        "created_timestamp": timestamp,
        "updated_timestamp": timestamp,
        "metadata": {
            "model": model_url,
            "config": project_config
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
