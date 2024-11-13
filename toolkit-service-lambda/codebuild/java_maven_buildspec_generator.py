from codebuild.buildspec_generator import BuildspecGenerator

import boto3
import os


class JavaMavenBuildspecGenerator(BuildspecGenerator):

    def generate_buildspec(self, project_id: str, service_info: dict) -> str:
        project_dir = self.create_project_dir(project_id)

        return self.write_buildspec(project_dir)

    def write_buildspec(self, project_dir: str):
        buildspec_path = os.path.join(project_dir, "buildspec.yaml")

        print(f"Writing buildspec.yaml to {buildspec_path}")

        ecr_path = os.getenv("ECR_REGISTRY_URI")
        ecr_registry_uri, ecr_repository_name = ecr_path.split("/", 1)
        aws_default_region = boto3.session.Session().region_name

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
  post_build:
    commands:
      - docker push $ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:latest
      - UNIQUE_FILE="imageDetail_$CODEBUILD_BUILD_ID.txt"
      - echo "IMAGE_URI=$ECR_REGISTRY_URI/$ECR_REPOSITORY_NAME:latest" > $UNIQUE_FILE
artifacts:
  files:
    - '**/*'
  base-directory: .
env:
  variables:
    ECR_REPOSITORY_NAME: {ecr_repository_name}
    ECR_REGISTRY_URI: {ecr_registry_uri}
    AWS_DEFAULT_REGION: {aws_default_region}
"""
        try:
            with open(buildspec_path, 'w') as f:
                f.write(buildspec_content)
            print(f"Buildspec written successfully to {buildspec_path}")
        except Exception as e:
            print(f"Failed to write buildspec.yaml: {e}")
            raise

        return buildspec_path
