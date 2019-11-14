from server.executors import BaseExecutor


class HttpExecutor(BaseExecutor):
    def __init__(self, start_endpoint: str, status_endpoint: str, runtime_endpoint: str, result_endpoint: str):
        super().__init__()
        self.start_endpoint = start_endpoint
        self.status_endpoint = status_endpoint
        self.runtime_endpoint = runtime_endpoint
        self.result_endpoint = result_endpoint

