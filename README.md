# Industry Toolkit

The Industry Toolkit is a comprehensive suite of tools designed to help developers build API-first, composable architectures. It streamlines the process of creating and managing APIs, SDKs, documentation, and server implementations across various languages.

## Documentation

For detailed documentation and to get started with the Industry Toolkit, please visit our [Wiki](https://github.com/aws/industry-toolkit/wiki).

## Quick Start

### Install the Industry Toolkit
The Industry Toolkit is installed as a CDK script. Before we get started, you'll need the following:

- AWS Credentials
- Github account and a [PAT created](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- Networking set up in your account that allows ECS tasks in a private subnet to reach ECR

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

Make note of the Lambda function name and the secrets ARN from the output; you'll need them in the next steps.

```bash
IndustryToolkitStack.CredentialsSecretArn = arn:aws:secretsmanager:<region>:<account>:secret:IndustryToolkitCredentials
IndustryToolkitStack.BootstraperLambdaName = IndustryToolkitStack-industrytoolkitbootstrapper-324234323

```

### Set your Github credentials
Create a Github PAT and store that as a key/value pair in the Secrets Manager secret that was created above. The key should be an identifier for the PAT and the value is the PAT itself:
```json
{"my-key": "<my-github-pat>"}
```

### Creating your First Service
Let's create a simple Spring Boot service that implements a [Shopping Cart API](https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/cart/model/cart.openapi.yaml).

Create a service definition file (service.json):
```bash service.json
{
  "service": {
    "type": "spring",
    "name": "my-shopping-cart",
    "description": "Shopping Cart service",
    "openapi": {
      "model": "https://raw.githubusercontent.com/aws-samples/industry-reference-models/refs/heads/main/domains/retail/models/cart/model/cart.openapi.yaml",
      "config": {
        "basePackage": "com.myorg.example",
        "modelPackage": "com.myorg.example.model",
        "apiPackage": "com.myorg.example.api",
        "invokerPackage": "com.myorg.example.configuration",
        "groupId": "com.myorg.example",
        "artifactId": "my-shopping-cart"
      }
    }
  },
  "scm": {
    "github": {
      "repo": "<github-repo-uri>",
      "secretKey": "my-key",
      "email": "none@none.com",
      "name": "Robot"
    }
  },
  "iac": {
    "cloudformation": {
      "vpc": "<my-vpc-id>",
      "subnets": "<my-subnet-id-1>,<my-subnet-id-2>,..."
    }
  }
}
```

Then execute the Service Bootstrapper Lambda:

```bash
aws lambda invoke \                                                                                                                           2.9m  Wed Nov 27 14:25:35 2024
      --function-name IndustryToolkitStack-industrytoolkitbootstrapper2C-jzOCXOQaQvbx  \
      --payload file://sservice.json \
      --cli-binary-format raw-in-base64-out \
      /dev/stdout
```

When this completes, you will have:
* A GitHub repo with your service code in it
* A CloudFormation script that will deploy your code as an ECS Fargate service
* An ECR Repository for your container images
* A CodePipeline that will fetch your source, compile/test/containerize, and deploy

For more in-depth documentation, visit our [Getting Started guide](https://github.com/aws/industry-toolkit/wiki/01:-Getting-Started).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

