from server.executors.http_executor import HttpExecutor


class SshExecutor(HttpExecutor):
    def __init__(
        self,
        user: str,
        password: str,
        remote_host: str,
        remote_port: int,
        local_port: int,
        request_endpoint: str,
        status_endpoint: str
    ):
        super().__init__(request_endpoint, status_endpoint)
        self.user = user
        self.password = password
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_port = local_port
