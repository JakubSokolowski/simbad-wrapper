from server.executors import BaseExecutor


class LocalExecutor(BaseExecutor):
    """
    Executor for executing task, for which binaries/jars/scripts are located on the same host as server
    """
    def __init__(self, executable_path: str):
        super().__init__()
        self.executable_path = executable_path
