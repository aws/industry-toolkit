from abc import ABC, abstractmethod
import os
import subprocess

class SourceRepo(ABC):
    @abstractmethod
    def create_repo(self):
        """Create a new repository."""
        pass

    @abstractmethod
    def commit(self, repo_dir: str, commit_message: str):
        """Commit changes to the GitHub repository."""
        pass
