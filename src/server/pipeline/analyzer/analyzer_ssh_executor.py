from sshtunnel import SSHTunnelForwarder

from models.simulation import Artifact
from server.pipeline.analyzer.analyzer_http_executor import AnalyzerHttpExecutor

SIMBAD_ANALYZER_POLLING_PERIOD = 60


class AnalyzerSshExecutor(AnalyzerHttpExecutor):
    def __init__(
            self,
            start_endpoint: str,
            status_endpoint: str,
            runtime_endpoint: str,
            result_endpoint: str,
            tunnel: SSHTunnelForwarder
    ):
        super().__init__(start_endpoint, status_endpoint, runtime_endpoint, result_endpoint)
        self.tunnel = tunnel

    def execute(self, in_file: Artifact) -> None:
        """
        Opens SSH tunnel and starts analyzer
        :param in_file: object representing output file of SIMBAD-CLI
        :return:
        """
        self.tunnel.start()
        super().execute(in_file)
        return

    def cleanup(self) -> None:
        """
        Closes SSH tunnel and cleans up intermediary artifacts
        :return:
        """
        self.tunnel.stop()
        return
