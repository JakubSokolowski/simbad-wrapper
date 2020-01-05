import threading
import json
from time import sleep

import requests

from models.analyzer_runtime_info import AnalyzerRuntimeInfo
from models.artifact import Artifact
from server.executors.http_executor import HttpExecutor

SIMBAD_ANALYZER_POLLING_PERIOD = 3


class AnalyzerHttpExecutor(HttpExecutor):
    def __init__(self, start_endpoint: str, status_endpoint: str, runtime_endpoint: str, result_endpoint: str):
        """
        Creates http executor for SIMBAD-ANALYZER
        :param start_endpoint: formatted string representing request endpoint
        :param status_endpoint: formatted string representing status endpoint
        """

        super().__init__(start_endpoint, status_endpoint, runtime_endpoint, result_endpoint)
        self.status: AnalyzerRuntimeInfo = AnalyzerRuntimeInfo(progress=0, is_finished=False)
        self.result = None
        self.is_finished = False

    def execute(self, in_file: Artifact) -> None:
        """
        Makes POST request to server to start process and starts polling in background for status change
        :param in_file: object representing output file of SIMBAD-CLI
        :return:
        """
        data = json.dumps({"path": in_file.path})
        response_status_code = requests.post(self.start_endpoint, data=data).status_code

        if response_status_code == 202:
            print(response_status_code)
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
            response = requests.get(self.runtime_endpoint).json()
            self.status = AnalyzerRuntimeInfo(is_finished=response['finished'], progress=response["progress"])
            if self.status.is_finished:
                # Stop polling, do not set set status to finished yet
                # Setting self.is_finished to true here might cause NoneType result
                # because task my ask for result as soon as sees this flag, but the result
                # was not returned yet from endpoint
                break
            sleep(SIMBAD_ANALYZER_POLLING_PERIOD)

        result_response = requests.get(self.result_endpoint).json()
        self.result = result_response
        self.is_finished = True
        return
