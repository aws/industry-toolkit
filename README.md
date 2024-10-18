# Industry Toolkit

The Industry Toolkit is a comprehensive suite of tools designed to help developers build API-first, composable architectures. It streamlines the process of creating and managing APIs, SDKs, documentation, and server implementations across various languages.

## Documentation

For detailed documentation and to get started with the Industry Toolkit, please visit our [Wiki](https://github.com/aws/industry-toolkit/wiki).

## Quick Start

### Install the Industry Toolkit
The Industry Toolkit is installed as a CDK script. Before we get started, you'll need the following:

- AWS Credentials
- Github account and a [PAT created](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

```bash
   # Clone this repository
   git clone https://github.com/aws/industry-toolkit.git
   
   # Install requirements
   cd tools/industry-toolkit
   python3 -m venv .venv
   source .venv/bin/activate
   pip3 install -r requirements.txt
   
   # Use CDK to deploy
   cdk synth
   cdk deploy
```

Make note of the endpoint URI and the secrets ARN from the output; you'll need them in the next steps.

```bash
IndustryToolkitStack.CredentialsSecretArn = arn:aws:secretsmanager:<region>:<account>:secret:IndustryToolkitCredentials
IndustryToolkitStack.IndustryToolkitApiEndpoint = https://<endpoint>.execute-api.<region>.amazonaws.com/prod/

```

### Set your Github credentials
Create a Github PAT and store that as a key/value pair in the Secrets Manager secret that was created above. The key should be an identifier for the PAT and the value is the PAT itself:
```json
{"my-key": "gh_adfa68a7sdf6adsfas8"}
```

### Creating your first Service
Let's create a simple Spring Boot service that implements a [Shopping Cart API](https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/cart/model/cart.openapi.yaml).

```bash
curl -X POST <my-endpoint>/services \
     -H "Content-Type: application/json" \
     -d '{
   "serviceName": "my-first-java-service",
   "serviceType": "spring",
   "description": "Tutorial",
   "model": "https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/cart/model/cart.openapi.yaml",
   "config": {
     "basePackage": "com.myorg",
     "modelPackage": "com.myorg.model",
     "apiPackage": "com.myorg.api",
     "invokerPackage": "com.myorg.configuration",
     "groupId": "com.myorg",
     "artifactId": "cart"
   },
   "target": {
     "org": "<github-org>",
     "secretKey": "<my-key>",
     "email": "none@none.com",
     "name": "Robot"
   }
  }'
```

You will receive a `202` status code and will see a project created in your Github org shortly. To check the status you can look at the CodeBuild task that was created.

For more in-depth documentation, visit our [Getting Started guide](https://github.com/aws/industry-toolkit/wiki/01:-Getting-Started).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

