from codebuild.buildspec_generator import BuildspecGenerator

import boto3
import os


class JavaMavenBuildspecGenerator(BuildspecGenerator):

    def generate_buildspec(self, project_id: str, service_info: dict) -> str:
        project_dir = self.create_project_dir(project_id)

        sts_client = boto3.client("sts")

        identity = sts_client.get_caller_identity()
        account_id = identity["Account"]

        return self.write_buildspec(project_dir, service_info["name"], account_id)

    def write_buildspec(self, project_dir: str, project_name:str, account_id: str):
        buildspec_path = os.path.join(project_dir, "buildspec.yaml")

        print(f"Writing buildspec.yaml to {buildspec_path}")

        region = boto3.session.Session().region_name

        ecr_registry_uri = f"{account_id}.dkr.ecr.{region}.amazonaws.com"
        ecr_repository_name = project_name

        buildspec_content = f"""
version: 0.2

phases:
  install:
    runtime-versions:
      java: 21
    commands:
      - echo "Installing Maven..."
      - mvn --version
  build:
    commands:
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY_URI
      - cd app
      - mvn clean install
      - docker build -t $ECR_REPOSITORY_NAME:latest -f Dockerfile .
      - docker tag $ECR_REPOSITORY_NAME:latest $ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:latest
      - docker tag $ECR_REPOSITORY_NAME:latest $ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - cd ..
  post_build:  
    commands:
      - docker push $ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:latest
      - docker push $ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:$CODEBUILD_RESOLVED_SOURCE_VERSION
      - echo Updating CloudFormation parameters file...
      - sed -i 's|PLACEHOLDER_URI|'${{ECR_REPOSITORY_URI}}/${{ECR_REPOSITORY_NAME}}:latest'|' infra/dev.json
      - cat infra/dev.json
artifacts:
  files:
    - infra/dev.json
    - infra/infra.yaml
base-directory: .

env:
  variables:
    ECR_REPOSITORY_NAME: {ecr_repository_name}
    ECR_REGISTRY_URI: {ecr_registry_uri}
    AWS_DEFAULT_REGION: {region}
"""
        try:
            with open(buildspec_path, 'w') as f:
                f.write(buildspec_content)
            print(f"Buildspec written successfully to {buildspec_path}")
        except Exception as e:
            print(f"Failed to write buildspec.yaml: {e}")
            raise

        return buildspec_path
