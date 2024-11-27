import os

from abc import ABC, abstractmethod


class BuildspecGenerator(ABC):

    @abstractmethod
    def generate_buildspec(self, project_id: str, service_info: dict) -> str:
        pass

    def create_project_dir(self, project_id: str) -> str:
        project_dir = f"/tmp/{project_id}"
        os.makedirs(project_dir, exist_ok=True)

        return project_dir
