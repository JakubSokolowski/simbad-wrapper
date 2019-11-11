from typing import List

from models.simulation import Artifact


class BaseExecutor:
    def __init__(self):
        self.is_finished = True
        self.result = None
        self.status = None

    def execute(self, in_file: Artifact) -> None:
        pass

    def get_status(self):
        return self.status

    def get_result(self) -> Artifact | List[Artifact]:
        return self.result
