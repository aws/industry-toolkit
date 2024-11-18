from abc import ABC, abstractmethod


class Registry(ABC):

    @abstractmethod
    def create_repository(self, repository_name: str):
        """
        Create a repository in the docker_registry.

        :param repository_name: Name of the repository to create.
        """
        pass
