# API Pipeline Blueprint

This blueprint allows you to create a pipeline that manages the entire lifecycle of an API that is defined in the [Smithy IDL](https://smithy.io/2.0/index.html).

## Getting Started

Getting started is easy! Create a new project with this blueprint, select and configure the language SDKs that you want to create, and modify your Smithy definition. Test your changes locally by running ./gradlew build. Finally push your changes to your remote - a workflow will run that builds and publishes your artifacts to CodeArtifact.


### Project Settings
| Setting      | Default | Description                                                                                                                                                                                                                                    |
|--------------| --- |------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| API Name     |  | This is the name of your API. Use something short, but descriptive, such as my-api. This will be used to create the Gradle project name, the project directory structure, built artifact packages, and documentation.                          |
| Service Name |  | Sets the name of your service. A service is typically named similar to an API. For example, a service for my-api would typically be named MyApiService.                                                                                        |
| Namespace    |  | Set the namespace of your API. This is usually company or organization specific, such as com.amazonaws. It will be used to set the generated code output directories, the generated artifact namespaces, and documentation. It is also used to |
| Description  |  | A short description (max 1024 characters) of your API. This will be used in documentation.                                                                                                                                                     |


### Supported Languages
New language support is being added all the time. The following languages are currently supported.

| Language   | Client SDK | Server SDK |
|:-----------|:----------:|:----------:|
| Typescript |     ✅      |            |
| Java       | ✅<br/>(preview) |            |

#### Typescript Client SDK
The Smithy TypeScript code generators provide the code generation framework to generate TypeScript artifacts (e.g. types, interfaces, implementations) of specified Smithy models.

| Setting                         | Default | Description                                                                                                       |
|---------------------------------|:-------:|-------------------------------------------------------------------------------------------------------------------|
| GenerateTypescriptClientSDK     |  false  | Generate Typescript types and client.                                                                             |
| GenerateTypescriptServerSDK     |  false  | Generate Typescript server implementation.                                                                        |
| Smithy Typescript Plugin Version| 0.20.1  | The version of the Smithy Typescript library.                                                                     |
| Typescript Namespace            |         | Override the namespace of the generated Typescript code. If not set will default to the global namespace setting. |


#### Versioning
Versioning is automatically handled by the generated workflow. Version numbers adhere to the SemVer versioning format. SemVer is a versioning scheme that conveys meaning about the underlying changes in a software release. It uses a three-part version number format: MAJOR.MINOR.PATCH, each representing different types of changes in the software:

* MAJOR version (X.Y.Z): Incremented when you make incompatible API changes. This signals to users that the new version is not backward-compatible with previous versions.
* MINOR version (X.Y.Z): Incremented when you add functionality in a backward-compatible manner. This means new features are added, but existing functionality remains unchanged.
* PATCH version (X.Y.Z): Incremented when you make backward-compatible bug fixes. These are typically small changes that do not add new features but resolve issues in the existing functionality.