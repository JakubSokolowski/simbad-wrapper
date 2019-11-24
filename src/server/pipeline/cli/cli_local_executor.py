import datetime
import os
import subprocess
import threading

import psutil

from models.simulation import Artifact, CliRuntimeInfo
from server.executors.local_executor import LocalExecutor


class CliLocalExecutor(LocalExecutor):
    def __init__(self, executable_path: str):
        """
        Creates local executor for SIMBAD-CLI
        :param executable_path: the path to executable
        :param workdir: the simulation workdir
        """
        super().__init__(executable_path)
        self.status: CliRuntimeInfo = CliRuntimeInfo(memory=0, cpu=0)
        self.result = None
        self.is_finished = False

    def execute(self, in_file: Artifact) -> None:
        """
        Executes SIMBAD-CLI binary in background thread
        :param in_file: the simulation configuration file
        :return:
        """
        thread = threading.Thread(target=self.run_cli, args=[in_file])
        thread.daemon = True
        thread.start()
        return

    def run_cli(self, conf: Artifact) -> None:
        self.status.step_id = conf.step_id
        out_path = '{}/cli_out.csv'.format(conf.get_workdir())
        conf_path = conf.path

        with open(out_path, 'w') as f:
            """
            Run SIMBAD-CLI binary with configuration as argument, and pipe stdout to cli_out.csv file
            Periodically update runtime info with psutil.
            """
            process = subprocess.Popen((self.executable_path, conf_path), stdout=subprocess.PIPE)
            process_info = psutil.Process(process.pid)
            counter = 0
            for c in iter(lambda: process.stdout.read(1), b''):
                counter += 1

                if counter % 1000000 == 0:
                    memory = process_info.memory_info().rss / 1000000
                    cpu = process_info.cpu_percent()
                    self.status.memory = memory
                    self.status.cpu = cpu
                    # TODO: parse some additional status data from stderr?

                line = c.decode('utf-8')
                f.write(line)

        end_timestamp = datetime.datetime.utcnow()
        self.result = Artifact(
            created_utc=end_timestamp,
            size_kb=os.path.getsize(out_path),
            path=out_path,
            step_id=conf.step_id,
            simulation_id=conf.simulation_id
        )
        self.is_finished = True
        return

