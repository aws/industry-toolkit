from abc import ABC, abstractmethod

class Pipeline(ABC):
    @abstractmethod
    def create_pipeline(self, pipeline_name: str, repository_name: str, branch_name: str, buildspec_location: str):
        """Abstract method to create a pipeline."""
        pass