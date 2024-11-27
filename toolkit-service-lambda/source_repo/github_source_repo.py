import os
import json
import boto3
import requests
import subprocess
import logging

from source_repo.source_repo import SourceRepo


class GitHubSourceRepo(SourceRepo):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    def __init__(self, scm_info):
        self.repo = scm_info['repo']
        self.email = scm_info['email']
        self.name = scm_info['name']
        self.secret_key = scm_info['secretKey']

        self.github_token = self._get_github_token(self.secret_key)

        os.environ['GITHUB_TOKEN'] = self.github_token

    def _get_github_token(self, secret_key):
        """Fetch the GitHub token from AWS Secrets Manager."""
        secret_name = os.environ['SCM_CREDENTIALS']
        client = boto3.client('secretsmanager', region_name=os.getenv("AWS_REGION"))
        secret_value = client.get_secret_value(SecretId=secret_name)
        secret = secret_value['SecretString']

        return json.loads(secret)[secret_key]

    def create_repo(self):
        service_name = self.repo.rstrip('/').split('/')[-1]
        url = f"https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "name": service_name,
            "private": True
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            print(f"Repository '{service_name}' created successfully under {self.repo}.")
        else:
            raise RuntimeError(f"Failed to create repository: {response.text}")

    def commit(self, repo_dir: str, commit_message: str):
        os.chdir(repo_dir)
        authenticated_repo_url = self.repo.replace("https://", f"https://{os.environ['GITHUB_TOKEN']}@")

        try:
            os.environ['HOME'] = '/tmp'
            self.logger.debug("Configuring Git default branch to 'main'.")
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=True)

            self.logger.info("Initializing new Git repository.")
            subprocess.run(["git", "init"], check=True)

            self.logger.debug(f"Setting Git user email to '{self.email}'.")
            subprocess.run(["git", "config", "user.email", self.email], check=True)

            self.logger.debug(f"Setting Git user name to '{self.name}'.")
            subprocess.run(["git", "config", "user.name", self.name], check=True)

            self.logger.debug("Adding remote origin with authenticated URL.")
            subprocess.run(["git", "remote", "add", "origin", authenticated_repo_url], check=True)

            self.logger.debug("Staging changes.")
            subprocess.run(["git", "add", "."], check=True)

            self.logger.debug(f"Committing changes with message: '{commit_message}'.")
            subprocess.run(["git", "commit", "-m", commit_message], check=True)

            self.logger.debug("Renaming branch to 'main'.")
            subprocess.run(["git", "branch", "-M", "main"], check=True)

            self.logger.debug("Pushing changes to remote repository.")
            push_result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)

            if push_result.returncode == 0:
                self.logger.info("Commit and push completed successfully.")
            else:
                self.logger.error(f"Push failed: {push_result.stderr}")

            self.logger.info("Commit and push completed successfully.")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git command failed: {e}")
