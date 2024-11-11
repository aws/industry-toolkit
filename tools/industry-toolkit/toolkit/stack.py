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

        # Random suffix for resource names that must be globaly unique, e.g. S3 buckets.
        random_suffix = str(uuid.uuid4())[:4].lower()

        # -------------------------
        # CloudFormation Parameters
        # -------------------------

        # Parameter for the CodeArtifact Domain Name
        domain_name_param = CfnParameter(self, "ArtifactsDomainName",
                                         type="String",
                                         default="industry-toolkitcode-artifact-domain",
                                         description="Name of the CodeArtifact domain."
                                         )

        # Parameter for the CodeArtifact Repository Name
        repo_name_param = CfnParameter(self, "ArtifactsRepositoryName",
                                       type="String",
                                       default="industry-toolkitcode-artifact-repo",
                                       description="Name of the CodeArtifact repository."
                                       )

        # Parameter for the artifacts S3 bucket
        artifacts_bucket_name_param = CfnParameter(self, "ArtifactsBucketName",
                                                   type="String",
                                                   default=f"industry-toolkit-artifacts-bucket-{random_suffix}",
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

        # Parameter for the Bootstrapper SQS queue name
        bootstrapper_queue_name_param = CfnParameter(self, "QueueName",
                                        type="String",
                                        default="industry-toolkit-bootstrapper-queue",
                                        description="The name of the SQS queue that API Gateway will send messages to."
        )

#         vpc_id_param = CfnParameter(self, "VpcId", type="String", description="The ID of an existing VPC to use.")



        # -------------------------
        # Artifact Repositories
        # -------------------------

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

        self.table = dynamodb.Table(
            self, "ServicesTable",
            table_name=f"IndustryToolkitServices-{random_suffix}",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # -------------------------
        # Bootstrapper Service
        # -------------------------
        dlq_queue = sqs.Queue(
                    self, "BootstrapperDLQ",
                    queue_name=f"{bootstrapper_queue_name_param.value_as_string}-dlq",
                    retention_period=Duration.days(14)
        )

        bootstrapper_input_queue = sqs.Queue(
            self,
            "BootstrapperServiceQueue",
            queue_name=bootstrapper_queue_name_param.value_as_string,
            visibility_timeout=Duration.seconds(300),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=1,
                queue=dlq_queue
            )
        )

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

#         lambda_function = lambda_.Function(
#             self, "IndustryToolkitBootstrapperLambda",
#             runtime=lambda_.Runtime.FROM_IMAGE,
#             code=lambda_.Code.from_asset_image(
#                 "toolkit/lambdas/bootstrapper/",
#                 file="Dockerfile"
#             ),
#             handler=lambda_.Handler.FROM_IMAGE,
#             memory_size=1024,
#             timeout=Duration.seconds(300),
#             environment={
#                 "LOG_LEVEL": bootstrapper_log_level_param.value_as_string,
#                 "CODEBUILD_ROLE_ARN": project_codebuild_role.role_arn,
#                 "CODEPIPELINE_ROLE_ARN": codepipeline_role.role_arn,
#                 "SCM_CREDENTIALS": github_pat_secret.secret_arn,
#                 "CODEPIPELINE_BUCKET": artifacts_bucket.bucket_name,
#                 "ECR_REGISTRY_URI": ecr_repository.repository_uri
#             }
#         )

#

#         vpc = ec2.Vpc.from_lookup(self, "Vpc", vpc_id=vpc_id_param.value_as_string)
#
#         cluster = ecs.Cluster(self, f"IndustryToolkitCluster-{random_suffix}", vpc=vpc)
#
#         ecs_task_role = iam.Role(
#             self, "EcsTaskRole",
#             assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
#             description="IAM role for the ECS task"
#         )
#
#         ecs_task_role.add_to_policy(iam.PolicyStatement(
#             actions=[
#                 "secretsmanager:GetSecretValue",
#                 "s3:*",
#                 "logs:*",
#                 "ecr:*",
#                 "ecs:*",
#                 "codebuild:*"],
#             resources=["*"]
#         ))
#
#         task_definition = ecs.FargateTaskDefinition(
#             self, "OnDemandTaskDefinition",
#             memory_limit_mib=1024,
#             cpu=512,
#             task_role=ecs_task_role
#         )
#
#         container = task_definition.add_container(
#             "IndustryToolkitContainer",
#             image=ecs.ContainerImage.from_registry(ecr_repository.repository_uri),
#             environment={
#                 "LOG_LEVEL": bootstrapper_log_level_param.value_as_string,
#                 "CODEBUILD_ROLE_ARN": project_codebuild_role.role_arn,
#                 "CODEPIPELINE_ROLE_ARN": codepipeline_role.role_arn,
#                 "SCM_CREDENTIALS": github_pat_secret.secret_arn,
#                 "CODEPIPELINE_BUCKET": artifacts_bucket.bucket_name,
#                 "ECR_REGISTRY_URI": ecr_repository.repository_uri
#             },
#             logging=ecs.LogDrivers.aws_logs(stream_prefix="IndustryToolkit")
#         )
#
#         container.add_port_mappings(ecs.PortMapping(container_port=5000))
#

        ecr_repository_test = ecr.Repository.from_repository_arn(
            self,
            "ECRRepository",
            repository_arn="arn:aws:ecr:us-west-2:211125507740:repository/greg/test-lambda-base"
        )

        lambda_function_test = lambda_.DockerImageFunction(
            self,
            "MyDockerLambdaFunction",
            code=lambda_.DockerImageCode.from_ecr(
                repository=ecr_repository_test,
                tag="latest"
            ),
            memory_size=1024,
            timeout=Duration.seconds(42),
            environment={
                "LOG_LEVEL": bootstrapper_log_level_param.value_as_string,
                "CODEBUILD_ROLE_ARN": project_codebuild_role.role_arn,
                "CODEPIPELINE_ROLE_ARN": codepipeline_role.role_arn,
                "SCM_CREDENTIALS": github_pat_secret.secret_arn,
                "CODEPIPELINE_BUCKET": artifacts_bucket.bucket_name,
                "ECR_REGISTRY_URI": ecr_repository.repository_uri
            },
        )

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

        api_gateway_role = iam.Role(
            self, "ApiGatewaySQSSendMessageRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            inline_policies={
                "SQSSendMessagePolicy": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "sqs:SendMessage",
                                "sqs:GetQueueAttributes",
                                "sqs:GetQueueUrl"
                            ],
                            resources=[bootstrapper_input_queue.queue_arn]
                        )
                    ]
                )
            }
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

        service_resource = api.root.add_resource("services")

        service_resource.add_method(
            "POST",
            apigateway.AwsIntegration(
                service="sqs",
                path=f"{self.account}/{bootstrapper_input_queue.queue_name}",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    credentials_role=api_gateway_role,
                    request_parameters={
                        "integration.request.header.Content-Type": "'application/x-www-form-urlencoded'"
                    },
                    request_templates={
                        "application/json": "Action=SendMessage&MessageBody=$util.urlEncode($input.json('$'))"
                    },
                    integration_responses=[
                        {
                            "statusCode": "202",
                            "selection_pattern": "2\\d{2}",
                            "response_templates": {
                                "application/json": """{
                                    "status": "Message sent to SQS successfully",
                                    "messageId": "$input.path('$.SendMessageResponse.SendMessageResult.MessageId')"
                                }"""
                            }
                        },
                        {
                            "statusCode": "500",
                            "selection_pattern": "5\\d{2}",
                            "response_templates": {
                                "application/json": """{
                                    "error": "Internal Server Error"
                                }"""
                            }
                        }
                    ]
                )
            ),
            method_responses=[
                {
                    "statusCode": "202",
                    "responseModels": {
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                },
                {
                    "statusCode": "500",
                    "responseModels": {
                        "application/json": apigateway.Model.EMPTY_MODEL
                    }
                }
            ]
        )

        bootstrapper_input_queue.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("apigateway.amazonaws.com")],
                actions=["sqs:SendMessage"],
                resources=[bootstrapper_input_queue.queue_arn]
            )
        )

        CfnOutput(self, "ArtifactsBucketNameOutput", value=artifacts_bucket.bucket_name, description="Artifacts S3 Bucket Name")
        CfnOutput(self, "EcrRepositoryUriOutput", value=ecr_repository.repository_uri, description="ECR Repository URI")
        CfnOutput(self, "ApiGatewayUrlOutput", value=api.url, description="API Gateway URL")
        CfnOutput(self, "SecretsManagerSecretArnOutput", value=github_pat_secret.secret_arn, description="Secrets Manager ARN")
        CfnOutput(self, "BootstrapperQueueUrlOutput", value=bootstrapper_input_queue.queue_url, description="SQS Queue URL")
        CfnOutput(self, "ApiGatewayLogGroupNameOutput", value=api_gateway_log_group.log_group_name, description="API Gateway Log Group")
