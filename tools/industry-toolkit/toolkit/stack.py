from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnParameter,
    CfnOutput,
    aws_apigateway as apigateway,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_codebuild as codebuild,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_logs as logs,
    Names
)
from constructs import Construct
import uuid


class IndustryToolkitStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        log_group_name_param = CfnParameter(self, "LogGroupPrefix",
            type="String",
            default="/tools/industrytoolkit/",
            description="Log group prefix for all Cloudwatch logs."
        )

        github_secret_name_param = CfnParameter(self, "IndustryToolkitSecretName",
            type="String",
            default="IndustryToolkitCredentials",
            description="Name of the Secrets Manager secret containing the secrets used by the toolkit."
        )

        codebuild_role_name_param = CfnParameter(self, "CodeBuildRoleName",
            type="String",
            default="IndustryToolkitCodeBuildRole",
            description="Name of the role the CodeBuild pipeline will use. This role will be created."
        )

        random_suffix = str(uuid.uuid4())[:4].lower()
        artifacts_bucket_name_param = CfnParameter(self, "ArtifactsBucketName",
            type="String",
            default=f"industry-toolkit-artifacts-bucket-{random_suffix}",
            description="Name of the S3 bucket for storing build artifacts. This bucket will be created."
        )

        log_group = logs.LogGroup(self, "ApiGatewayAccessLogs",
                                  log_group_name=log_group_name_param.value_as_string + 'apigateway',
                                  removal_policy=RemovalPolicy.DESTROY)

        cloudwatch_logs_role = iam.Role(self, "ApiGatewayCloudWatchRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonAPIGatewayPushToCloudWatchLogs")
            ]
        )

        api_gateway_account = apigateway.CfnAccount(self, "ApiGatewayAccount",
            cloud_watch_role_arn=cloudwatch_logs_role.role_arn
        )

        artifacts_bucket = s3.Bucket(self, "IndustryToolkitArtifactsBucket",
                                     bucket_name=artifacts_bucket_name_param.value_as_string)

        github_pat_secret = secretsmanager.Secret(
            self, "IndustryToolkitCredentials",
            description="Credentials for the Industry Toolkit",
            secret_name=github_secret_name_param.value_as_string
        )

        codebuild_role = iam.Role(
            self, "IndustryToolkitCodeBuildRole",
            role_name=codebuild_role_name_param.value_as_string,
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
        )

        artifacts_bucket.grant_read_write(codebuild_role)
        github_pat_secret.grant_read(codebuild_role)

        codebuild_project = codebuild.Project(
            self, "IndustryToolkitCodeBuildProject",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "commands": [
                            "npm install -g @openapitools/openapi-generator-cli"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            "echo 'Fetching GitHub credentials...'",
                            f"export GITHUB_TOKEN=$(aws secretsmanager get-secret-value --secret-id {github_pat_secret.secret_arn} --query 'SecretString' --output text | jq -r '.\"'\"$SECRET_KEY\"'\"')"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo 'Decoding the CONFIG map...'",
                            "export DECODED_CONFIG=$(echo \"$CONFIG\" | jq -r 'to_entries | map(\"\\(.key)=\\(.value | @sh)\") | join(\",\")')",
                            "echo $DECODED_CONFIG",
                            "bash -c 'if [ -n \"$CONFIG\" ] && [ \"$DECODED_CONFIG\" != \"\" ]; then openapi-generator-cli generate -i $MODEL -g $SERVICE_TYPE -o /tmp/generated --additional-properties \"$DECODED_CONFIG\" || exit 1; else openapi-generator-cli generate -i $MODEL -g $SERVICE_TYPE -o /tmp/generated || exit 1; fi'"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "curl -H \"Authorization: token $GITHUB_TOKEN\" https://api.github.com/user/repos -d \"{\\\"name\\\": \\\"$SERVICE_NAME\\\", \\\"private\\\": true}\"",
                            "cd /tmp/generated",
                            "git config --global init.defaultBranch main",
                            "git init",
                            "git config --global user.email \"$TARGET_EMAIL\"",
                            "git config --global user.name \"$TARGET_NAME\"",
                            "git remote add origin https://$GITHUB_TOKEN@github.com/$TARGET_ORG/$SERVICE_NAME.git",
                            "git add .",
                            "git commit -m 'Initial Commit'",
                            "git branch -M main",
                            "git push -u origin main"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "/tmp/generated/**"
                    ]
                }
            }),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
                compute_type=codebuild.ComputeType.SMALL,
                privileged=True
            ),
            cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
            role=codebuild_role
        )

        codebuild_task = tasks.CodeBuildStartBuild(
            self, "IndustryToolkitInvokeCodeBuild",
            project=codebuild_project,
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            environment_variables_override={
                "SERVICE_NAME": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.serviceName")
                ),
                "SERVICE_TYPE": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.serviceType")
                ),
                "DESCRIPTION": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.description")
                ),
                "MODEL": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.model")
                ),
                "CONFIG": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.json_to_string(sfn.JsonPath.string_at("$.config"))
                ),
                "TARGET_ORG": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.target.org")
                ),
                "SECRET_KEY": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.target.secretKey")
                ),
                "TARGET_EMAIL": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.target.email")
                ),
                "TARGET_NAME": codebuild.BuildEnvironmentVariable(
                    value=sfn.JsonPath.string_at("$.target.name")
                )
            },
            result_path="$.BuildResult"
        )

        step_function = sfn.StateMachine(
            self, "IndustryToolkitStepFunction",
            definition_body=sfn.DefinitionBody.from_chainable(codebuild_task)
        )

        api_gateway_role = iam.Role(
            self, "IndustryToolkitApiGatewayInvokeStepFunctionsRole",
            assumed_by=iam.ServicePrincipal("apigateway.amazonaws.com"),
            inline_policies={
                "InvokeStepFunctions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["states:StartExecution"],
                            resources=[step_function.state_machine_arn]
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
                access_log_destination=apigateway.LogGroupLogDestination(log_group),
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
                    "target": {
                        "type": apigateway.JsonSchemaType.OBJECT,
                        "properties": {
                            "org": {"type": apigateway.JsonSchemaType.STRING},
                            "email": {"type": apigateway.JsonSchemaType.STRING},
                            "name": {"type": apigateway.JsonSchemaType.STRING}
                        }
                    }
                },
                "required": ["serviceName", "serviceType", "description", "model", "target"]
            }
        )

        service_resource = api.root.add_resource("services")

        service_resource.add_method(
            "POST",
            apigateway.AwsIntegration(
                service="states",
                action="StartExecution",
                integration_http_method="POST",
                options=apigateway.IntegrationOptions(
                    credentials_role=api_gateway_role,
                    request_templates={
                        "application/json": """
                        {
                            "input": "$util.escapeJavaScript($input.body)",
                            "stateMachineArn": "%s"
                        }
                        """ % step_function.state_machine_arn,
                    },
                    integration_responses=[
                        {
                            "statusCode": "202",
                            "selection_pattern": "2\\d{2}",
                            "response_templates": {
                                "application/json": """{
                                    "output": $input.body
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
            request_models={"application/json": request_model},
            request_validator=api.add_request_validator(
                "RequestValidator",
                validate_request_body=True
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

        CfnOutput(self, "CredentialsSecretArn",
                    value=github_pat_secret.secret_arn,
                    description="The ARN of the credentials Secret in Secrets Manager"
        )
