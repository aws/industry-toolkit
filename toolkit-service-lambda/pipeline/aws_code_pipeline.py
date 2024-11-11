import boto3
import os
import json
from pipeline.pipeline import Pipeline

class AwsCodePipeline(Pipeline):
    def __init__(self):
        self.codepipeline_client = boto3.client('codepipeline')
        self.codebuild_client = boto3.client('codebuild')

    def create_pipeline(self, pipeline_name: str, repository_name: str, branch_name: str, buildspec_location: str):
        unique_artifact_name = "imageDetail.txt"  # Static name; the unique ID will be embedded by CodePipeline

        build_project = self.codebuild_client.create_project(
            name=f"{pipeline_name}-build",
            source={
                'type': 'CODEPIPELINE'
            },
            artifacts={
                'type': 'CODEPIPELINE',
                'namespaceType': 'BUILD_ID'
            },
            environment={
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/standard:5.0',
                'computeType': 'BUILD_GENERAL1_SMALL',
                'environmentVariables': [
                    {'name': 'ENV', 'value': 'dev', 'type': 'PLAINTEXT'}
                ]
            },
            logsConfig={
                'cloudWatchLogs': {
                    'status': 'ENABLED',
                    'groupName': f"/aws/codebuild/{pipeline_name}-build",
                    'streamName': '{build-id}'
                },
                's3Logs': {
                    'status': 'DISABLED'
                }
            },
            serviceRole=os.environ['CODEBUILD_ROLE_ARN'],
        )

        pipeline_definition = {
            'name': pipeline_name,
            'roleArn': os.environ['CODEPIPELINE_ROLE_ARN'],
            'artifactStore': {
                'type': 'S3',
                'location': os.environ['CODEPIPELINE_BUCKET']
            },
            'stages': [
                {
                    'name': 'Source',
                    'actions': [
                        {
                            'name': 'SourceAction',
                            'actionTypeId': {
                                'category': 'Source',
                                'owner': 'ThirdParty',
                                'provider': 'GitHub',
                                'version': '1'
                            },
                            'configuration': {
                                'Owner': repository_name.split('/')[0],
                                'Repo': repository_name.split('/')[1],
                                'Branch': branch_name,
                                'OAuthToken': os.environ['GITHUB_TOKEN']
                            },
                            'outputArtifacts': [{'name': 'SourceOutput'}],
                            'runOrder': 1
                        }
                    ]
                },
                {
                    'name': 'Build',
                    'actions': [
                        {
                            'name': 'BuildAction',
                            'actionTypeId': {
                                'category': 'Build',
                                'owner': 'AWS',
                                'provider': 'CodeBuild',
                                'version': '1'
                            },
                            'configuration': {
                                'ProjectName': build_project['project']['name']
                            },
                            'inputArtifacts': [{'name': 'SourceOutput'}],
                            'outputArtifacts': [{'name': 'BuildOutput'}],
                            'runOrder': 1
                        }
                    ]
                },
                {
                    'name': 'Deploy',
                    'actions': [
                        {
                            'name': 'DeployAction',
                            'actionTypeId': {
                                'category': 'Deploy',
                                'owner': 'AWS',
                                'provider': 'CloudFormation',
                                'version': '1'
                            },
                            'configuration': {
                                'ActionMode': 'CREATE_UPDATE',
                                'StackName': f"{pipeline_name}-stack",
                                'TemplatePath': 'BuildOutput::infra/infra.yaml',
                                'Capabilities': 'CAPABILITY_IAM',
                                'ParameterOverrides': json.dumps({
                                    'ImageUri': '211125507740.dkr.ecr.us-west-2.amazonaws.com/industry-toolkit-ecr-registry:latest'
                                }),
                                'RoleArn': os.environ['CODEPIPELINE_ROLE_ARN']
                            },
                            'inputArtifacts': [{'name': 'BuildOutput'}],
                            'runOrder': 1
                        }
                    ]
                }
            ]
        }

        response = self.codepipeline_client.create_pipeline(pipeline=pipeline_definition)
        return response