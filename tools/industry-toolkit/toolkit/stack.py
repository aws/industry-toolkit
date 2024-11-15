from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    CfnParameter,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_apigateway as apigateway,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_codebuild as codebuild,
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_lambda_event_sources as event_sources,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_codeartifact as codeartifact,
    aws_iam as iam,
    aws_logs as logs,
    aws_ecr as ecr,
    aws_sqs as sqs,
    Names
)
from constructs import Construct
import uuid


class IndustryToolkitStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # -------------------------
        # CloudFormation Parameters
        # -------------------------

        suffix_param = CfnParameter(
            self,
            "Suffix",
            type="String",
            default=str(uuid.uuid4())[:8],
            description="Unique suffix for resources requiring a globally unique name"
        )

        # Parameter for the CodeArtifact Domain Name
        domain_name_param = CfnParameter(self, "ArtifactsDomainName",
                                         type="String",
                                         default="industry-toolkit-code-artifact-domain",
                                         description="Name of the CodeArtifact domain."
                                         )

        # Parameter for the CodeArtifact Repository Name
        repo_name_param = CfnParameter(self, "ArtifactsRepositoryName",
                                       type="String",
                                       default="industry-toolkit-code-artifact-repo",
                                       description="Name of the CodeArtifact repository."
                                       )

        # Parameter for the artifacts S3 bucket
        artifacts_bucket_name_param = CfnParameter(self, "ArtifactsBucketName",
                                                   type="String",
                                                   description="Name of the S3 bucket used to store build artifacts and logs."
                                                   )

        # Parameter for the ECR registry name
        ecr_registry_name = CfnParameter(self, "ArtifactsEcrRegistryName",
                                         type="String",
                                         default="industry-toolkit-ecr-registry",
                                         description="Log level for Lambda function. Default is DEBUG."
                                         )

        # Parameter for Bootstraper service log level
        bootstrapper_log_level_param = CfnParameter(self, "LogLevel",
                                                    type="String",
                                                    default="DEBUG",
                                                    description="Log level for Bootstrapper Lambda function. Default is DEBUG."
                                                    )

        # Parameter for the Secrets Manager secret that stores credentials
        secret_name_param = CfnParameter(self, "IndustryToolkitSecretName",
                                         type="String",
                                         default="industry-toolkit-credentials",
                                         description="Name of the Secrets Manager secret containing the secrets used by the toolkit."
                                         )
        # Parameter for the prefix for all cloudwatch logs
        log_group_name_param = CfnParameter(self, "LogGroupPrefix",
                                        type="String",
                                        default="/tools/industrytoolkit/",
                                        description="Log group prefix for all Cloudwatch logs."
                                        )

        # -------------------------
        # Artifact Repositories
        # -------------------------
        bucket_name = artifacts_bucket_name_param.value_as_string or f"industry-toolkit-artifacts-bucket-{str(uuid.uuid4())[:8]}"
        artifacts_bucket = s3.Bucket(self, "ArtifactsBucket",
                                     bucket_name=artifacts_bucket_name_param.value_as_string)

        ecr_repository = ecr.Repository(
            self,
            "ArtifactsEcrRepository",
            repository_name=ecr_registry_name.value_as_string,
            removal_policy=RemovalPolicy.RETAIN
        )

        github_pat_secret = secretsmanager.Secret(
            self, "IndustryToolkitCredentials",
            description="Credentials for the Industry Toolkit",
            secret_name=secret_name_param.value_as_string
        )

        services_table = dynamodb.Table(
            self, "ServicesTable",
            table_name=f"IndustryToolkitServices-{suffix_param.value_as_string}",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True
        )

        # -------------------------
        # Bootstrapper Service
        # -------------------------

        project_codebuild_role = iam.Role(
            self, "ProjectCodeBuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="IAM role for CodeBuild with access to necessary resources"
        )

        project_codebuild_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "codebuild:CreateReportGroup",
                "codebuild:CreateReport",
                "codebuild:BatchPutTestCases",
                "codebuild:UpdateReport",
                "logs:*",
                "s3:*",
                "secretsmanager:GetSecretValue",
                "ecr:*",
                "ec2:*"
            ],
            resources=["*"]
        ))

        codepipeline_role = iam.Role(
            self, "IndustryToolkitCodePipelineRole",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            description="IAM role for CodePipeline with access to S3, CodeBuild, and other required services"
        )

        codepipeline_role.assume_role_policy.add_statements(iam.PolicyStatement(
            actions=["sts:AssumeRole"],
            principals=[iam.ServicePrincipal("cloudformation.amazonaws.com")]
        ))

        codepipeline_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "cloudformation:*",
                "ecs:*",
                "s3:*",
                "codebuild:*",
                "secretsmanager:GetSecretValue",
                "iam:PassRole",
                "ec2:*",
                "logs:*",
                "iam:*",
                "iam:DeleteRolePolicy",
                "iam:DeleteRole",
                "iam:CreateRole"
            ],
            resources=["*"]
        ))


        repo = ecr.Repository.from_repository_arn(
            self, "IndustryToolkitRepo",
            "arn:aws:ecr:us-west-2:211125507740:repository/industry-toolkit/service-lambda-handler"
        )

        image_digest = "sha256:4907758cc94fbbc0c8021cf0e1a7a25faa131d063b0da7f653a1c6dfeb76ec64"

        lambda_function_test = lambda_.Function(
            self,
            "MyDockerLambdaFunction",
            code=lambda_.Code.from_ecr_image(repository=repo, tag_or_digest=image_digest),
            handler=lambda_.Handler.FROM_IMAGE,
            runtime=lambda_.Runtime.FROM_IMAGE,
            memory_size=1024,
            timeout=Duration.seconds(300),
            environment={
                "LOG_LEVEL": bootstrapper_log_level_param.value_as_string,
                "CODEBUILD_ROLE_ARN": project_codebuild_role.role_arn,
                "CODEPIPELINE_ROLE_ARN": codepipeline_role.role_arn,
                "SCM_CREDENTIALS": github_pat_secret.secret_arn,
                "CODEPIPELINE_BUCKET": artifacts_bucket.bucket_name,
                "ECR_REGISTRY_URI": ecr_repository.repository_uri,
                "SERVICES_TABLE_NAME": services_table.table_name
            },
        )

        services_table.grant_read_write_data(lambda_function_test)
        github_pat_secret.grant_read(lambda_function_test)

        codebuild_codepipeline_policy = iam.PolicyStatement(
            actions=[
                "codebuild:*",
                "codepipeline:*"
            ],
            resources=["*"]
        )

        lambda_function_test.add_to_role_policy(codebuild_codepipeline_policy)

        lambda_function_test.add_to_role_policy(iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=[project_codebuild_role.role_arn]
        ))

        lambda_function_test.add_to_role_policy(iam.PolicyStatement(
            actions=["iam:PassRole"],
            resources=[codepipeline_role.role_arn]
        ))

        lambda_function_test.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["*"]
        ))

        # -------------------------
        # API Gateway
        # -------------------------

        api_gateway_log_group = logs.LogGroup(self, "ApiGatewayAccessLogs",
                                  log_group_name=log_group_name_param.value_as_string + 'apigateway',
                                  removal_policy=RemovalPolicy.DESTROY)

        cloudwatch_logs_role = iam.Role(self, "ApiGatewayCloudWatchRole",
                                        assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
                                        managed_policies=[
                                            iam.ManagedPolicy.from_aws_managed_policy_name(
                                                "service-role/AmazonAPIGatewayPushToCloudWatchLogs")
                                        ]
                                        )

        api_gateway_account = apigateway.CfnAccount(self, "ApiGatewayAccount",
                                                    cloud_watch_role_arn=cloudwatch_logs_role.role_arn
                                                    )


        api = apigateway.RestApi(self, "IndustryToolkitApi",
             deploy_options=apigateway.StageOptions(
                 logging_level=apigateway.MethodLoggingLevel.INFO,
                 data_trace_enabled=True,
                 metrics_enabled=True,
                 access_log_destination=apigateway.LogGroupLogDestination(api_gateway_log_group),
                 access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                     caller=True,
                     http_method=True,
                     ip=True,
                     protocol=True,
                     request_time=True,
                     resource_path=True,
                     response_length=True,
                     status=True,
                     user=True
                 )
             )
             )


        request_model = api.add_model(
            "RequestModel",
            content_type="application/json",
            schema={
                "type": apigateway.JsonSchemaType.OBJECT,
                "properties": {
                    "serviceName": {"type": apigateway.JsonSchemaType.STRING},
                    "serviceType": {"type": apigateway.JsonSchemaType.STRING},
                    "description": {"type": apigateway.JsonSchemaType.STRING},
                    "model": {"type": apigateway.JsonSchemaType.STRING},
                    "config": {"type": apigateway.JsonSchemaType.OBJECT, "additionalProperties": True},
                    "target": {"type": apigateway.JsonSchemaType.OBJECT, "additionalProperties": True}
                },
                "required": ["serviceName", "serviceType", "description", "model", "target"]
            }
        )

        service_resource = api.root.add_resource("{proxy+}")

        service_resource.add_method(
            "ANY",
            apigateway.LambdaIntegration(
                lambda_function_test,
                proxy=True
            )
        )

        api.root.add_method(
            "ANY",
            apigateway.LambdaIntegration(
                lambda_function_test,
                proxy=True
            )
        )

        CfnOutput(self, "ArtifactsBucketNameOutput", value=artifacts_bucket.bucket_name, description="Artifacts S3 Bucket Name")
        CfnOutput(self, "EcrRepositoryUriOutput", value=ecr_repository.repository_uri, description="ECR Repository URI")
        CfnOutput(self, "ApiGatewayUrlOutput", value=api.url, description="API Gateway URL")
        CfnOutput(self, "SecretsManagerSecretArnOutput", value=github_pat_secret.secret_arn, description="Secrets Manager ARN")
        CfnOutput(self, "ApiGatewayLogGroupNameOutput", value=api_gateway_log_group.log_group_name, description="API Gateway Log Group")
