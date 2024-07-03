import {
  AccountConnection,
  Environment,
  EnvironmentDefinition,
  Role,
} from '@amazon-codecatalyst/blueprint-component.environments';

import {
  SourceRepository,
  SourceFile, SubstitionAsset, StaticAsset, File,
} from '@amazon-codecatalyst/blueprint-component.source-repositories';

import {
  convertToWorkflowEnvironment,
  Workflow,
  WorkflowBuilder,
} from '@amazon-codecatalyst/blueprint-component.workflows';

import {
  Blueprint as ParentBlueprint,
  Options as ParentOptions,
  Region,
} from '@amazon-codecatalyst/blueprints.blueprint';
import defaults from './defaults.json';

export interface Options extends ParentOptions {
  /**
   * @displayName Environment Configuration
   * Create an environment that will be used for Workflow steps such as building, packaging, and publishing SDKs.
   */
  environment: EnvironmentDefinition<{
    /**
     * @displayName AWS Account
     * An AWS account is needed to create or assign a role from.
     */
    awsAccount: AccountConnection<{
      /**
       * @displayName IAM Role
       * A role that has the permissions to perform any steps in your workflows.
       */
      role: Role<[]>;
    }>;
  }>;

  /**
   * This is the name of your API. Use something short, but descriptive, such as my-api. This will be used to create
   * the Gradle project name, the project directory structure, and documentation. This will also be the name of the
   * generated artifact that gets published to your artifact repository.
   * @displayName API Name
   * @validationRegex /^[a-z][a-z-]*$/
   * @validationMessage Must start with a lowercase letter, and can only contain lowercase letters and hyphens.
   */
  apiName: string;

  /**
   * Sets the name of your service. A service is typically named similar to an API. For example, a service for my-api
   * would typically be named MyApiService.
   * @displayName Service Name
   * @validationRegex /^[A-Z][a-zA-Z0-9]{0,63}$/
   * @validationMessage Must start with a capital letter, and can contain up to 64 characters. Cannot contain spaces.
   */
  serviceName: string;

  /**
   * Set the namespace of your API. This is usually company or organization specific, such as com.amazonaws. It will be
   * used to set the generated code output directories, the generated artifact namespaces, and documentation.
   * @displayName Namespace
   * @validationRegex /^[a-z][a-z.]*[^.]$/
   * @validationMessage Must start with a lowercase letter, and can only contain lowercase letters and periods.
   * Must end with a letter.
   */
  namespace: string;

  /**
   * Write a short description (max 1024 characters) of your API. This will be used in documentation.
   * @displayName Description
   * @textArea
   * @validationRegex /^.{0,1024}$/
   * @validationMessage Can contain any characters, but cannot exceed 1024 characters.
   */
  description: string;

  /**
   * Enable generation of Typescript client SDK.
   * @displayName Typescript SDK Generation
   */
  typescriptSdk: {
    /**
     * Enable generation of Typescript client SDK.
     * @displayName Generate Typescript Client SDK
     */
    generateTypescriptClient: boolean;

    /**
     * Set the version of the Smithy Typescript library.
     * @displayName Smithy Typescript CodeGen Library Version
     */
    smithyTypescriptPluginVersion?: string;

    /**
     * Override the namespace of the generated Typescript code. If not set will default to the global
     * namespace setting.
     * @displayName Typescript Code Namespace Override
     */
    typescriptNamespace?: string;
  };

  /**
   * !!! Experimental - Generated code is subject to change !!!
   * Enable generation of Java client SDK.
   * @displayName Java SDK Generation
   */
  javaSdk: {
    /**
     * Create a Java client SDK.
     * @displayName Generate Java Client SDK
     */
    generateJavaClient: boolean;

    /**
     * Set the version of the Smithy Java library.
     * @displayName Smithy Java CodeGen Library Version
     */
    smithyJavaPluginVersion?: string;

    /**
     * Override the namespace of the generated Java code. If not set will default to the global namespace
     * setting.
     * @displayName Java Code Namespace Override
     */
    javaNamespace?: string;
  };


  /**
   * Enable the generation of an OpenAPI definition. You can specify the OpenAPI version of the definition
   * to generate.
   * @displayName OpenAPI
   */
  openApi: {
    /**
     * Generates an OpenAPI definition file in the specified version.
     * @displayName Generate OpenAPI definition.
     */
    generateOpenApiDefinition: boolean;

    /**
     * Set the version of the Smithy OpenAPI library.
     * @displayName Smithy OpenAPI Plugin Version
     */
    smithyOpenApiPluginVersion?: string;

    /**
     * Set the OpenAPI version for the generated API definition.
     * @displayName OpenAPI Version
     */
    openApiVersion: '3.0.2' | '3.1.0';
  };

  publishing: {
    /**
     * The domain that holds the CodeArtifact repository.
     * @displayName Code Artifact Domain
     */
    codeArtifactDomain: string;

    /**
     * Set the CodeArtifact repository name to publish to. Artifacts will be published as
     * <api-name>-<language>:<version>.
     * @displayName Code Artifact Repository
     */
    codeArtifactRepo: string;

    /**
     * The region the CodeArtifact repository is in.
     * @displayName Code Artifact Region
     */
    region: Region<['*']>;
  };

  /**
   * @displayName Additional Configuration
   * @collapsed true
   */
  additionalConfiguration: {
    /**
     * Specify the version of Smithy core libraries to use.
     * @displayName Smithy Core Libraries Version
     */
    smithyVersion?: string;

    /**
     * Specify the version of the Smithy Gradle plugin to use.
     * @displayName Smithy Plugin Version
     */
    smithyPluginVersion?: string;

    /**
     * Set the name of the created repository. If not set, will default to API Name.
     * @displayName Override Repository Name
     */
    repoName?: string;
  };

}

export class Blueprint extends ParentBlueprint {
  constructor(options_: Options) {
    super(options_);
    console.log(defaults);

    // Create repository. Repository name will default to API Name, but can be overridden.
    let repoName: string =
        options_.additionalConfiguration.repoName === null ||
        options_.additionalConfiguration.repoName === undefined ||
        options_.additionalConfiguration.repoName === ''
          ? options_.apiName
          : options_.additionalConfiguration.repoName;

    const repository = new SourceRepository(this, { title: repoName });

    // Copy all mandatory project files to the repository.
    StaticAsset.findAll('project-assets/**/*').forEach(asset => {
      new SourceFile(repository, asset.path().replace(/^project-assets\//, ''), asset.content().toString());
    });

    // Copy Gradle files to the repository.
    new File(repository, 'gradlew', new StaticAsset('gradle/gradlew').content());
    new File(repository, 'gradlew.bat', new StaticAsset('gradle/gradlew.bat').content());
    new File(repository, 'gradle/wrapper/gradle-wrapper.properties',
      new StaticAsset('gradle/gradle/wrapper/gradle-wrapper.properties').content());
    new File(repository, 'gradle/wrapper/gradle-wrapper.jar',
      new StaticAsset('gradle/gradle/wrapper/gradle-wrapper.jar').content());

    // Create README.md file.
    new SourceFile(repository, 'README.md',
      new SubstitionAsset('project-assets/README.md').substitute({
        apiName: options_.apiName,
        description: options_.description,
      }));

    // Create smithy-build.json file.
    new SourceFile(repository, 'smithy-build.json',
      generateSmithyBuildJson(options_),
    );

    // Create .gitignore file.
    new SourceFile(repository, '.gitignore',
      new StaticAsset('templates/.gitignore.template').toString());

    // Create build.gradle file.
    new SourceFile(repository, 'build.gradle',
      new SubstitionAsset('project-assets/build.gradle').substitute({
        plugins: generateGradlePlugins(options_),
        dependencies: generateGradleDependencies(options_),
        publishing: generateGradlePublishingConfig(options_, options_.apiName),
      }));

    // Create settings.gradle file
    new SourceFile(repository, 'settings.gradle',
      new SubstitionAsset('project-assets/settings.gradle').substitute({
        apiName: options_.apiName,
      }));

    // Create a starter Smithy definition file.
    new SourceFile(repository, 'src/main/smithy/model.smithy',
      new SubstitionAsset('project-assets/src/main/smithy/model.smithy').substitute({
        namespace: options_.namespace,
        serviceName: options_.serviceName,
        description: options_.description,
      }));

    // Dynamic steps based on which SDKs builds are selected
    // Copy required Java build files if Java SDK build is selected.
    if (options_.javaSdk.generateJavaClient) {
      StaticAsset.findAll('build-assets/java/**/*').forEach(asset => {
        new SourceFile(repository, asset.path(), new SubstitionAsset(asset.path()).substitute(
          {
            javaNamespace: options_.javaSdk.javaNamespace,
            publishing: generateGradlePublishingConfig(options_, options_.apiName + '-java'),
            apiName: options_.apiName,
          },
        ));
      });
    }

    const workflowName = options_.apiName + '-build-sdk';
    const workflowBuilder = new WorkflowBuilder(this);

    workflowBuilder.setName(workflowName);
    workflowBuilder.addBranchTrigger(['main']);

    let environment: Environment | undefined = undefined;
    if (options_.environment) {
      environment = new Environment(this, options_.environment);
    }

    let steps: string[] = [];

    let awsAccount = options_.environment.awsAccount?.id;
    let region = options_.publishing.region;
    let domain = options_.publishing.codeArtifactDomain;

    steps.push(`export CODEARTIFACT_AUTH_TOKEN=\`aws codeartifact get-authorization-token --domain ${domain} --domain-owner ${awsAccount} --region ${region} --query authorizationToken --output text\``);

    steps.push(...[
      'chmod +x release.sh',
      './release.sh publish',
      'export VERSION=$(cat version)',
    ]);

    workflowBuilder.addBuildAction({
      actionName: 'generate_source',
      environment: environment && convertToWorkflowEnvironment(environment),
      input: {
        Sources: ['WorkflowSource'],
      },
      steps: steps,
      output: {
        Variables: ['VERSION'],
        Artifacts: artifactConfig(options_).Artifacts,
      },
    });

    if (options_.typescriptSdk.generateTypescriptClient) {
      workflowBuilder.addBuildAction({
        actionName: 'build_typescript_package',
        environment: environment && convertToWorkflowEnvironment(environment),
        dependsOn: ['generate_source'],
        input: {
          Sources: [],
          Artifacts: ['typescript_source'],
          Variables: {
            VERSION: '${generate_source.VERSION}',
          },
        },
        steps: [
          'cd ./build/smithyprojections/' + options_.apiName + '/source/typescript-client-codegen',
          'npm install yarn -g',
          'yarn && yarn prepack',
          'aws codeartifact login --tool npm --repository ' + options_.publishing.codeArtifactRepo + ' --domain ' + options_.publishing.codeArtifactRepo + ' --domain-owner ' + options_.environment.awsAccount?.id + ' --region ' + options_.publishing.region + '',
          'echo always-auth=true >> ~/.npmrc',
          'yarn version --new-version $VERSION',
          'yarn publish',
        ],
        output: { },
      });
    }

    if (options_.javaSdk.generateJavaClient) {
      workflowBuilder.addBuildAction({
        actionName: 'build_java_package',
        environment: environment && convertToWorkflowEnvironment(environment),
        dependsOn: ['generate_source'],
        input: {
          Sources: [],
          Artifacts: ['java_source'],
          Variables: {
            VERSION: '${generate_source.VERSION}',
          },
        },
        steps: [
          'export CODEARTIFACT_AUTH_TOKEN=`aws codeartifact get-authorization-token ' +
          '--domain ' + options_.publishing.codeArtifactRepo + ' --domain-owner ' + options_.environment.awsAccount?.id + ' --region '
           + options_.publishing.region + ' --query authorizationToken --output text`',
          'mkdir workspace',
          'mv ./build-assets/java/* workspace/',
          'mv gradlew workspace/',
          'mv ./build/smithyprojections/' + options_.apiName + '/source/java-client-codegen/* workspace/',
          'mv ./gradle workspace/',
          'cd workspace',
          'chmod +x gradlew',
          './gradlew publish -Pversion=$VERSION',
          'jar tf ./build/libs/*.jar',
        ],
        output: {},
      });
    }

    new Workflow(this, repository, workflowBuilder.getDefinition());
  }
}

interface Artifact {
  Name: string;
  Files: string[];
}

function artifactConfig(options_: Options): { Artifacts: Artifact[] } {
  const artifacts: Artifact[] = [];

  if (options_.javaSdk.generateJavaClient) {
    artifacts.push({
      Name: 'java_source',
      Files: [
        `./build/smithyprojections/${options_.apiName}/source/java-client-codegen/**/*`,
        './build-assets/java/**/*',
        './gradlew',
        './gradle/**/*',
      ],
    });
  }

  if (options_.typescriptSdk.generateTypescriptClient) {
    artifacts.push({
      Name: 'typescript_source',
      Files: [
        `./build/smithyprojections/${options_.apiName}/source/typescript-client-codegen/**/*`,
      ],
    });
  }

  return { Artifacts: artifacts };
}

function generateGradlePublishingConfig(options: Options, artifactId: string): string {
  let groupId = options.namespace;

  let codeArtifactRepo = options.publishing.codeArtifactRepo;
  let accountNumber = options.environment.awsAccount?.id;
  let region = options.publishing.region;

  return `
publishing {
    publications {
        mavenJava(MavenPublication) {
            groupId = '${groupId}'
            artifactId = '${artifactId}'
            version = project.hasProperty('version') ? project.property('version') : '0.0.0'
            from components.java
        }
    }
    repositories {
        maven {
            url 'https://${codeArtifactRepo}-${accountNumber}.d.codeartifact.${region}.amazonaws.com/maven/${codeArtifactRepo}/'
            credentials {
                username "aws"
                password System.env.CODEARTIFACT_AUTH_TOKEN
            }
        }
    }
}`;
}

function generateGradleDependencies(options: Options): string {
  let dependencies = '\timplementation(\"software.amazon.smithy:smithy-cli:'
      + options.additionalConfiguration.smithyVersion + '\")\n';

  dependencies += '\timplementation(\"software.amazon.smithy:smithy-aws-traits:'
      + options.additionalConfiguration.smithyVersion + '\")\n';

  if (options.openApi.generateOpenApiDefinition) {
    dependencies += '\timplementation(\"software.amazon.smithy:smithy-openapi:'
      + options.openApi.smithyOpenApiPluginVersion + '\")\n';
  }

  if (options.typescriptSdk.generateTypescriptClient) {
    dependencies += '\timplementation(\"software.amazon.smithy.typescript:smithy-typescript-codegen:'
      + options.typescriptSdk.smithyTypescriptPluginVersion + '\")\n';
  }

  if (options.javaSdk.generateJavaClient) {
    dependencies += '\timplementation(\"io.github.smithy4j:smithy-java:'
        + options.javaSdk.smithyJavaPluginVersion + '\")\n';
  }

  return dependencies;
}

function generateGradlePlugins(options: Options): string {
  let plugins = '\tid \'software.amazon.smithy\' version \'' + options.additionalConfiguration.smithyPluginVersion + '\'\n';
  plugins += '\tid \'maven-publish\'';

  return plugins;
}

function generateSmithyBuildJson(options: Options): string {
  const config: SmithyBuildJson = {
    version: '1.0',
    plugins: {
      model: {
        service: options.namespace + '#' + options.serviceName,
        outputDirectory: 'build/models/json',
        prettyPrint: true,
      },
    },
  };

  if (options.openApi.generateOpenApiDefinition) {
    config.plugins.openapi = {
      service: options.namespace + '#' + options.serviceName,
      version: options.openApi.openApiVersion,
      outputDirectory: 'build/openapi',
    };
  }

  if (options.typescriptSdk.generateTypescriptClient) {
    config.plugins['typescript-client-codegen'] = {
      service: options.namespace + '#' + options.serviceName,
      package: '@' + (options.typescriptSdk.typescriptNamespace || options.namespace) + '/' + options.apiName + '-typescript',
      packageVersion: '0.0.0',
    };
  }

  if (options.javaSdk.generateJavaClient) {
    config.plugins['java-client-codegen'] = {
      service: options.namespace + '#' + options.serviceName,
      module: options.serviceName,
      moduleDescription: options.description,
      moduleVersion: '0.0.0',
    };
  }

  return JSON.stringify(config, null, 2);
}

interface SmithyBuildJson {
  version: string;
  plugins: {
    model: {
      service: string;
      outputDirectory: string;
      prettyPrint: boolean;
    };
    openapi?: {
      service: string;
      version: string;
      outputDirectory: string;
    };
    'typescript-client-codegen'?: {
      service: string;
      package: string;
      packageVersion: string;
    };
    'java-client-codegen'?: {
      service: string;
      module: string;
      moduleDescription: string;
      moduleVersion: string;
    };
  };
}