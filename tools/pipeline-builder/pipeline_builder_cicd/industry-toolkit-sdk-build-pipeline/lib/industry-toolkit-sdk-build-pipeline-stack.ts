import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import * as codeartifact from 'aws-cdk-lib/aws-codeartifact';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';

export class IndustryToolkitSdkBuildPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    // GitHub owner and repo name stored using AWS Systems Manager Parameter Store, and github token stored securely using AWS Secrets Manager.  
    const owner = ssm.StringParameter.valueFromLookup(this, 'github-owner');
    const repo = ssm.StringParameter.valueFromLookup(this, 'github-repo');
    const githubConnection = ssm.StringParameter.valueFromLookup(this, 'github-connection');

    // S3 bucket for artifacts
    const artifactBucket = new s3.Bucket(this, 'industryToolkitBuildArtifactBucket', {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true
    });

    // S3 bucket for scripts
    const scriptsBucket = new s3.Bucket(this, 'ITR-SciptsBucket', {
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true
    });

    // Add files from 'scripts/' local directory to artifactBucket s3 bucket using s3deploy
    new s3deploy.BucketDeployment(this, 'AddScripts', {
      sources: [s3deploy.Source.asset('scripts')],
      destinationBucket: scriptsBucket,
      destinationKeyPrefix: 'scripts'
    });
    

    // CodeArtifact Domain
    const domain = new codeartifact.CfnDomain(this, 'industryToolkitCodeArtifactDomain', {
      domainName: 'industry-toolkit-retail-domain',
    });

    // CodeArtifact repo to have an external connection to the public NPM JS repo, to be used upstream by private repos
    const npmUpstreamRepo = new codeartifact.CfnRepository(this, 'industryToolkitNpmUpstreamRepo', {
      domainName: domain.attrName,
      repositoryName: 'npm-upstream',
      externalConnections: ['public:npmjs'],
    });

    // CodeArtifact repo to have an external connection to the public nuget repo, to be used upstream by private repos
    const nugetUpstreamRepo = new codeartifact.CfnRepository(this, 'industryToolkitNugetUpstreamRepo', {
      domainName: domain.attrName,
      repositoryName: 'nuget-upstream',
      externalConnections: ['public:nuget-org'],
    });

    // CodeArtifact repo to have an external connection to the public maven repo, to be used upstream by private repos
    const mavenUpstreamRepo = new codeartifact.CfnRepository(this, 'industryToolkitMavenUpstreamRepo', {
      domainName: domain.attrName,
      repositoryName: 'maven-upstream',
      externalConnections: ['public:maven-central'],
    });

    // CodeArtifact Repository
    const repository = new codeartifact.CfnRepository(this, 'industryToolkitCodeArtifactRepository', {
      domainName: domain.attrName,
      repositoryName: 'industry-toolkit-retail-repository',
      upstreams: [npmUpstreamRepo.repositoryName, nugetUpstreamRepo.repositoryName, mavenUpstreamRepo.repositoryName]
    });

    // Add all CodeArtifact upstream repositories with connections to public registries (npm, nuget, maven) as dependencies to ensure they are created before the CodeArtifact repository
    repository.addDependency(npmUpstreamRepo);
    repository.addDependency(nugetUpstreamRepo);
    repository.addDependency(mavenUpstreamRepo);

    // Define the source artifacts
    const sourceOutput = new codepipeline.Artifact();
    const s3SourceOutput = new codepipeline.Artifact();

    // Define the build artifacts
    const setSdkVersionOutput = new codepipeline.Artifact();
    const tsBuildOutput = new codepipeline.Artifact();
    const dotNetBuildOutput = new codepipeline.Artifact();
    const javaBuildOutput = new codepipeline.Artifact();

    // CodeBuild check commit message format
    const checkCommitMessage = new codebuild.PipelineProject(this, 'checkCommitMessage', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/check_commit_message.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
    });

    // CodeBuild set SDK version step
    const setSdkVersion = new codebuild.PipelineProject(this, 'setSdkVersion', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/set_sdk_version.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
      environmentVariables: {
        ARTIFACT_REGION: { value: this.region },
        ARTIFACT_DOMAIN_OWNER: { value: domain.attrOwner },
        ARTIFACT_DOMAIN: { value: domain.attrName },
        ARTIFACT_REPO: { value: repository.attrName }
      }
    });

    // CodeBuild typescript SDK build step
    const tsSdkBuild = new codebuild.PipelineProject(this, 'tsSdkBuild', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/ts_sdk_build.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
      // Pass environment variables to CodeBuild project
      environmentVariables: {
        ARTIFACT_REPO: { value: repository.attrName },
        ARTIFACT_DOMAIN_OWNER: { value: domain.attrOwner },
        ARTIFACT_DOMAIN: { value: domain.attrName },
        ARTIFACT_REGION: { value: this.region }
      }
    });

    // CodeBuild dotNet SDK build step
    const dotNetSdkBuild = new codebuild.PipelineProject(this, 'dotNetSdkBuild', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/dotNet_sdk_build.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
      // Pass environment variables to CodeBuild project
      environmentVariables: {
        ARTIFACT_REPO: { value: repository.attrName },
        ARTIFACT_DOMAIN_OWNER: { value: domain.attrOwner },
        ARTIFACT_DOMAIN: { value: domain.attrName },
        ARTIFACT_REGION: { value: this.region }
      }
    });

    // CodeBuild Java SDK build step
    const javaSdkBuild = new codebuild.PipelineProject(this, 'javaSdkBuild', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/java_sdk_build.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
      // Pass environment variables to CodeBuild project
      environmentVariables: {
        ARTIFACT_REPO: { value: repository.attrName },
        ARTIFACT_DOMAIN_OWNER: { value: domain.attrOwner },
        ARTIFACT_DOMAIN: { value: domain.attrName },
        ARTIFACT_REGION: { value: this.region }
      }
    });

    // CodeBuild step to tag repository with version tag
    const tagRepository = new codebuild.PipelineProject(this, 'tagRepository', {
      buildSpec: codebuild.BuildSpec.fromAsset('build-files/tag_repository.yaml'),
      environment: {
        buildImage: codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
      },
      // Pass environment variables to CodeBuild project
      environmentVariables: {
        ARTIFACT_REPO: { value: repository.attrName },
        ARTIFACT_DOMAIN_OWNER: { value: domain.attrOwner },
        ARTIFACT_DOMAIN: { value: domain.attrName },
        ARTIFACT_REGION: { value: this.region }
      }
    });

    // Add upstream repositories to CodeArtifact repo
    repository.addDependency(npmUpstreamRepo);
    repository.addDependency(nugetUpstreamRepo);

    // Grant permissions for CodeBuild to access CodeArtifact for setting SDK version, then tag the repo with version number
    setSdkVersion.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'codeartifact:GetAuthorizationToken',
        'codeartifact:ReadFromRepository',
        'codeartifact:GetRepositoryEndpoint',
        'sts:GetServiceBearerToken',
        'codeartifact:ListTagsForResource'
      ],
      resources: [
        domain.attrArn,
        repository.attrArn
      ]
    }));

    setSdkVersion.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'sts:GetServiceBearerToken'
      ],
      resources: [
        '*'
      ],
      conditions: {
        'StringEquals': {
          'sts:AWSServiceName': 'codeartifact.amazonaws.com'
        }
      }
    }));


    // Grant permissions for CodeBuild to publish to CodeArtifact
    tsSdkBuild.role?.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AWSCodeArtifactReadOnlyAccess'));

    tsSdkBuild.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'codeartifact:PublishPackageVersion',
        'codeartifact:PutPackageMetadata',
        'codeartifact:GetAuthorizationToken',
        'codeartifact:GetRepositoryEndpoint',
        'sts:GetServiceBearerToken'
      ],
      resources: [
        domain.attrArn,
        repository.attrArn,
        `arn:aws:codeartifact:${this.region}:${domain.attrOwner}:package/${domain.attrName}/${repository.attrName}/npm/*`
      ]
    }));

    dotNetSdkBuild.role?.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AWSCodeArtifactReadOnlyAccess'));

    dotNetSdkBuild.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'codeartifact:PublishPackageVersion',
        'codeartifact:PutPackageMetadata',
        'codeartifact:GetAuthorizationToken',
        'codeartifact:GetRepositoryEndpoint',
        'sts:GetServiceBearerToken'
      ],
      resources: [
        domain.attrArn,
        repository.attrArn,
        `arn:aws:codeartifact:${this.region}:${domain.attrOwner}:package/${domain.attrName}/${repository.attrName}/nuget/*`
      ]
    }));

    javaSdkBuild.role?.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AWSCodeArtifactReadOnlyAccess'));

    javaSdkBuild.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'codeartifact:PublishPackageVersion',
        'codeartifact:PutPackageMetadata',
        'codeartifact:GetAuthorizationToken',
        'codeartifact:GetRepositoryEndpoint',
        'sts:GetServiceBearerToken'
      ],
      resources: [
        domain.attrArn,
        repository.attrArn,
        `arn:aws:codeartifact:${this.region}:${domain.attrOwner}:package/${domain.attrName}/${repository.attrName}/maven/*`
      ]
    }));

    tagRepository.role?.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AWSCodeArtifactReadOnlyAccess'));

    tagRepository.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'codeartifact:TagResource',
        'codeartifact:GetAuthorizationToken',
        'codeartifact:GetRepositoryEndpoint',
        'sts:GetServiceBearerToken'
      ],
      resources: [
        domain.attrArn,
        repository.attrArn
      ]
    }));

    // Define the pipeline
    const pipeline = new codepipeline.Pipeline(this, 'industryToolkitSdkBuildPipeline', {
      artifactBucket: artifactBucket,
      stages: [
        {
          stageName: 'Source',
          actions: [
            new codepipeline_actions.CodeStarConnectionsSourceAction({
              actionName: 'GitHub_Source',
              owner: owner,
              repo: repo,
              connectionArn: githubConnection,
              output: sourceOutput,
              branch: 'main',
              codeBuildCloneOutput: true,
              variablesNamespace: 'SOURCE_VARIABLES'
            }),
            new codepipeline_actions.S3SourceAction({
              actionName: 'Scripts_Source',
              bucket: scriptsBucket,
              bucketKey: 'scripts/scripts.zip',
              output: s3SourceOutput,
              trigger: codepipeline_actions.S3Trigger.NONE
              
            })
          ],
        },
          {
            stageName: 'Check_Commit_Message',
            actions: [
              new codepipeline_actions.CodeBuildAction({
                actionName: 'Check_Commit_Message',
                project: checkCommitMessage,
                input: sourceOutput,
                extraInputs: [s3SourceOutput],
                variablesNamespace: 'CHECK_COMMIT_MESSAGE',
                environmentVariables: {
                  COMMIT_MSG: { value: '#{SOURCE_VARIABLES.CommitMessage}' }
                }
              }),
            ],
          },
        {
          stageName: 'Set_Version',
          actions: [
            new codepipeline_actions.CodeBuildAction({
              actionName: 'Set_SDK_Version',
              variablesNamespace: 'SET_SDK_VERSION',
              project: setSdkVersion,
              input: sourceOutput,
              extraInputs: [s3SourceOutput],
              outputs: [setSdkVersionOutput],
              environmentVariables: {
                COMMIT_TYPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_TYPE}' },
                COMMIT_SCOPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SCOPE}' },
                COMMIT_SUBJECT: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SUBJECT}' },
                COMMIT_BODY: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_BODY}' },
                COMMIT_FOOTER: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_FOOTER}' }
              }
            }),
          ],
        },
        {
          stageName: 'Build_SDKs',
          actions: [
            new codepipeline_actions.CodeBuildAction({
              actionName: 'TS_SDK_Build',
              project: tsSdkBuild,
              input: sourceOutput,
              extraInputs: [s3SourceOutput],
              outputs: [tsBuildOutput],
              environmentVariables: {
                SDK_VERSION: { value: '#{SET_SDK_VERSION.SDK_VERSION}' },
                COMMIT_SCOPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SCOPE}' }
              }
            }),
            new codepipeline_actions.CodeBuildAction({
              actionName: 'DotNet_SDK_Build',
              project: dotNetSdkBuild,
              input: sourceOutput,
              outputs: [dotNetBuildOutput],
              environmentVariables: {
                SDK_VERSION: { value: '#{SET_SDK_VERSION.SDK_VERSION}' },
                COMMIT_SCOPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SCOPE}' }
              }
            }),
            new codepipeline_actions.CodeBuildAction({
              actionName: 'Java_SDK_Build',
              project: javaSdkBuild,
              input: sourceOutput,
              outputs: [javaBuildOutput],
              environmentVariables: {
                SDK_VERSION: { value: '#{SET_SDK_VERSION.SDK_VERSION}' },
                COMMIT_SCOPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SCOPE}' }
              }
            }),
          ],
        },
        {
          stageName: 'Tag_Repository',
          actions: [
            new codepipeline_actions.CodeBuildAction({
              actionName: 'Tag_Repository',
              project: tagRepository,
              input: sourceOutput,
              environmentVariables: {
                SDK_VERSION: { value: '#{SET_SDK_VERSION.SDK_VERSION}' },
                COMMIT_SCOPE: { value: '#{CHECK_COMMIT_MESSAGE.COMMIT_SCOPE}' },
                REPO_ARN: { value: '#{SET_SDK_VERSION.REPO_ARN}' }
              }
            }),
          ],
        },
      ],
    });

    // Output the pipeline URL
    new cdk.CfnOutput(this, 'PipelineURL', {
      value: 'https://'+this.region+'.console.aws.amazon.com/codesuite/codepipeline/pipelines/'+pipeline.pipelineName+'/view?region='+this.region
    });

  }
}
