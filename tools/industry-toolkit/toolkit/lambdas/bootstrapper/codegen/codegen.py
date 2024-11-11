from abc import ABC, abstractmethod

class Codegen(ABC):
    @abstractmethod
    def generate_project(self, project_id: str, event: dict):
        """Generates a project based on the provided event data."""
        pass