from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    Duration,
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

        git_secret = secretsmanager.Secret(
            self, "GitHubPATSecret",
            secret_name="github-pat",
            description="Secret for storing GitHub Personal Access Token (PAT)"
        )

        pipeline_builder_layer = _lambda.LayerVersion(
            self, "PipelineBuilderLayer",
            code=_lambda.Code.from_asset("pipeline_builder_layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Layer containing Python libraries for Pipeline Builder",
        )

        git_layer = _lambda.LayerVersion.from_layer_version_arn(self, "GitLayer",
            "arn:aws:lambda:us-west-2:553035198032:layer:git-lambda2:8"
        )

        project_generator_lambda = _lambda.Function(
            self, "PipelineBuilderLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            code=_lambda.Code.from_asset("pipeline_builder_lambda"),
            timeout=Duration.minutes(5),
            handler="pipeline_builder_lambda.handler",
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "GIT_SECRET_ARN": git_secret.secret_arn
            },
            layers=[
                pipeline_builder_layer,
                git_layer
            ]
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

        bucket.grant_read_write(project_generator_lambda)
        git_secret.grant_read(project_generator_lambda)
        project_generator_lambda.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
        project_generator_lambda.add_to_role_policy(iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    resources=["*"]
                ))
