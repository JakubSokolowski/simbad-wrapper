from server.executors import BaseExecutor


class LocalExecutor(BaseExecutor):
    def __init__(self, executable_path: str):
        super().__init__()
        self.executable_path = executable_path
