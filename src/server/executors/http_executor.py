from server.executors import BaseExecutor


class HttpExecutor(BaseExecutor):
    def __init__(self, request_endpoint: str, status_endpoint: str):
        self.request_endpoint = request_endpoint
        self.status_endpoint = status_endpoint

