import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from registry import Registry

class EcrRegistry(Registry):

    def __init__(self):
        self.region = os.environ.get("AWS_REGION")
        self.ecr_client = boto3.client("ecr", region_name=self.region)


    def create_repository(self, repository_name: str):
        try:
            ecr_client = boto3.client("ecr", region_name=region)

            response = ecr_client.create_repository(
                repositoryName=repository_name
            )

            repository = response["repository"]
            print(f"Repository {repository_name} created successfully!")
            print(f"Repository URI: {repository['repositoryUri']}")
            return repository

        except ecr_client.exceptions.RepositoryAlreadyExistsException:
            print(f"Repository '{repository_name}' already exists.")
        except NoCredentialsError:
            print("AWS credentials not found. Ensure they are configured.")
        except PartialCredentialsError:
            print("Incomplete AWS credentials configuration.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
