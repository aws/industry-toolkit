import os

from abc import ABC, abstractmethod


class DockerfileGenerator(ABC):

    @abstractmethod
    def generate_dockerfile(self, project_id: str) -> str:
        pass

    def write_dockerfile(self, project_id, dockerfile_content: str):
        project_dir = f"/tmp/{project_id}/app"
        os.makedirs(project_dir, exist_ok=True)

        dockerfile_path = os.path.join(project_dir, "Dockerfile")

        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)

        return dockerfile_path
