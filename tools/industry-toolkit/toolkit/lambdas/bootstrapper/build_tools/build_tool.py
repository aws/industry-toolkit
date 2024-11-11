from abc import ABC, abstractmethod

class BuildTool(ABC):
    @abstractmethod
    def write_config_files(self, project_dir: str):
        """Configure the build tool to publish an image to ECR."""
        pass