from abc import ABC, abstractmethod


class Pipeline(ABC):
    @abstractmethod
    def create_pipeline(self, service_info: dict, scm_info: dict):
        """Abstract method to create a pipeline."""
        pass
