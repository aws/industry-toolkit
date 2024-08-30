import json
import os
import boto3
from git import Repo
from cookiecutter.main import cookiecutter

def handler(event, context):
    secrets_client = boto3.client('secretsmanager')
    secret_arn = os.environ['GIT_SECRET_ARN']
    secret_value = secrets_client.get_secret_value(SecretId=secret_arn)
    git_credentials = json.loads(secret_value['SecretString'])

    config = json.loads(event['body'])

    repo_name = config['gitRepo']['repoName']
    org = config['gitRepo']['org']
    branch = config['gitRepo'].get('branch', 'main')

    template_repo_url = config['templateRepo']['url']
    subdirectory = config['templateRepo'].get('subdirectory', '')

    local_repo_path = f'/tmp/{repo_name}'
    Repo.clone_from(template_repo_url, local_repo_path, env={
        'GIT_USERNAME': git_credentials['username'],
        'GIT_PASSWORD': git_credentials['password']
    })

    if subdirectory:
        template_path = os.path.join(local_repo_path, subdirectory)
    else:
        template_path = local_repo_path

    cookiecutter_context = config['context']
    cookiecutter(
        template_path,
        no_input=True,
        extra_context=cookiecutter_context
    )

    new_repo = Repo.init(local_repo_path)
    new_repo.git.add(all=True)
    new_repo.index.commit("Initial commit")
    new_repo.create_remote('origin', f'git@github.com:{org}/{repo_name}.git')
    new_repo.git.push('origin', branch)
