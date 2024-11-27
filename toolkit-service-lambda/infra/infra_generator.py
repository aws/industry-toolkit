import os

from abc import ABC, abstractmethod


class InfraGenerator(ABC):

    @abstractmethod
    def generate_infra(self, project_id: str, infra_config: dict) -> str:
        pass

    def create_infra_dir(self, project_id: str) -> str:
        project_dir = f"/tmp/{project_id}/infra"
        os.makedirs(project_dir, exist_ok=True)

        return project_dir
