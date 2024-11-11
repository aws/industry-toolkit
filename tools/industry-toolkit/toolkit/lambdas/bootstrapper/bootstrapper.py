import subprocess
import logging
import json
import uuid
import os

from pipeline.pipeline import Pipeline
from urllib.parse import urlparse

from codegen.open_api_codegen import OpenApiCodegen
from codebuild.java_maven_pipeline_generator import JavaMavenPipelineGenerator
from build_tools.maven_build_tool import MavenBuildTool
from pipeline.aws_code_pipeline import AwsCodePipeline
from docker.java_spring_boot_generator import JavaSpringBootDockerfileGenerator
from infra.cloudformation_infra_generator import CloudFormationInfraGenerator
from source_repo.github_source_repo import GitHubSourceRepo

def lambda_handler(event, context):
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level, logging.INFO)

    logging.basicConfig(level=log_level)
    logger = logging.getLogger()

    logger.debug("Received event: %s", json.dumps(event))

    for record in event.get("Records", []):
        message_body = json.loads(record["body"])

        project_id = str(uuid.uuid4())
        logger.info("Creating project with id %s", project_id)

        project_dir = f"/tmp/{project_id}"
        app_dir = f"{project_dir}/app"
        os.makedirs(app_dir, exist_ok=True)

        project_type = message_body.get('serviceType')
        project_config = message_body.get('config', {})

        service_name = message_body.get('serviceName')
        model_url = message_body.get('model')
        target_info = message_body.get('target')

        if project_type == 'spring':
            generator = JavaSpringBootDockerfileGenerator()
            infra_generator = CloudFormationInfraGenerator()
        else:
            raise ValueError(f"Unsupported project type: {project_type}")

        logger.info("Creating repo: %s...", target_info["repo"])
        repo = GitHubSourceRepo(target_info)
        repo.create_repo()

        codegen = OpenApiCodegen()
        codegen.generate_project(project_id, message_body)

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

        logger.info("Project created successfully for service %s", service_name)

    return {
        'status': 'success',
        'message': f"Processed {len(event.get('Records', []))} records from SQS"
    }
