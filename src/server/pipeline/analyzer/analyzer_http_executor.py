import threading
from time import sleep

import requests

from models.simulation import Artifact, AnalyzerRuntimeInfo
from server.executors.http_executor import HttpExecutor

SIMBAD_ANALYZER_POLLING_PERIOD = 60


class AnalyzerHttpExecutor(HttpExecutor):
    def __init__(self, start_endpoint: str, status_endpoint: str, runtime_endpoint: str, result_endpoint: str):
        """
        Creates http executor for SIMBAD-ANALYZER
        :param start_endpoint: formatted string representing request endpoint
        :param status_endpoint: formatted string representing status endpoint
        """

        super().__init__(start_endpoint, status_endpoint, runtime_endpoint, result_endpoint)
        self.status: AnalyzerRuntimeInfo = AnalyzerRuntimeInfo(progress=0)
        self.result = None
        self.is_finished = False

    def execute(self, in_file: Artifact) -> None:
        """
        Makes POST request to server to start process and starts polling in background for status change
        :param in_file: object representing output file of SIMBAD-CLI
        :return:
        """

        response_status_code = requests.post(self.start_endpoint, {"path": in_file.path}).status_code

        if response_status_code == 202:
            # start request was accepted, start polling for status changes
            thread = threading.Thread(target=self.update_runtime_info)
            thread.daemon = True
            thread.start()
        else:
            print('ERROR')
        return

    def is_busy(self) -> bool:
        """
        check whether analyzer is busy by getting the status endpoint response
        :return: flag indicating whether analyzer is busy
        """
        # check whether analyzer is busy
        response = requests.get(self.status_endpoint).json()
        analyzer_status = response['status']
        return analyzer_status == 'BUSY'

    def update_runtime_info(self) -> None:
        """
        Periodically update analyzer runtime info by making GET request to runtime info endpoint
        :return:
        """
        while self.is_finished is not True:
            response = requests.get(self.status_endpoint).json()
            self.status = AnalyzerRuntimeInfo(**response)
            self.is_finished = self.status.is_finished
            sleep(SIMBAD_ANALYZER_POLLING_PERIOD)

        result_response = requests.get(self.result_endpoint).json()
        self.result = result_response['artifacts']
        return
