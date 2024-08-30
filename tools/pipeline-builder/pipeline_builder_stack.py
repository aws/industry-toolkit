from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
)
from constructs import Construct

class PipelineBuilderStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket(self, "ProjectArtifactsBucket", versioned=True)

        git_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitCredentialsSecret", "git-credentials"
        )

        project_generator_lambda = _lambda.Function(
            self, "PipelineBuilderLambda",
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset("pipeline_builder_lambda"),  # Updated to the new directory name
            handler="pipeline_builder_lambda.handler",
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "GIT_SECRET_ARN": git_secret.secret_arn
            }
        )

        api = apigateway.RestApi(
            self, "PipelineBuilderApi",
            rest_api_name="Pipeline Builder Service",
            description="This service generates software projects from templates."
        )
        project = api.root.add_resource("project")
        project.add_method("POST", apigateway.LambdaIntegration(project_generator_lambda))

        build_project = codebuild.Project(
            self, "BuildProject",
            source=codebuild.Source.git_hub(
                owner="example-org",
                repo="example-repo"
            ),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_5_0
            )
        )

        pipeline = codepipeline.Pipeline(self, "Pipeline", pipeline_name="ProjectPipeline")

        bucket.grant_read_write(project_generator_lambda)
        git_secret.grant_read(project_generator_lambda)
        project_generator_lambda.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
