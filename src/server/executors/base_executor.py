from typing import List, Union

from models.artifact import Artifact


class BaseExecutor:
    """
    Base class for executing tasks in different environments
    """
    def __init__(self):
        self.is_finished = False
        self.result = None
        self.status = None
        self.log = None

    def execute(self, in_file: Artifact) -> None:
        pass

    def cleanup(self) -> None:
        pass
