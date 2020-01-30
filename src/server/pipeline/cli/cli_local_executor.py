import datetime
import os
import subprocess
import sys
import threading

import psutil

from models.artifact import Artifact
from models.cli_runtime_info import CliRuntimeInfo
from server.executors.local_executor import LocalExecutor


class CliLocalExecutor(LocalExecutor):
    def __init__(self, executable_path: str):
        """
        Creates local executor for SIMBAD-CLI
        :param executable_path: the path to executable
        :param workdir: the simulation workdir
        """
        super().__init__(executable_path)
        self.status: CliRuntimeInfo = CliRuntimeInfo(memory=0, cpu=0, progress=0)
        self.result = None
        self.is_finished = False
        self.log = None

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

    def update_progress(self, workdir, process: subprocess.Popen):
        # simulator_log = open(workdir + '/logs/simulator.log', "a")
        process_info = psutil.Process(process.pid)
        for line in iter(lambda: process.stderr.readline(), b''):
            # simulator_log.write(line.decode('utf-8'))
            try:
                curr, target = line.decode('utf8').split('/')

                # TODO The CPU reading may show above 100% - find out if this can be adjusted
                memory = process_info.memory_info().rss
                cpu = process_info.cpu_percent()
                self.status.memory = memory
                self.status.cpu = cpu
                self.status.progress = int(float(int(curr) / int(target)) * 100.0)
            except ValueError:
                print('Error in simulator: \n {}'.format(line))
                self.status.error = 'Unexpected stderr output in simulator'
                # simulator_log.close()
                return
        # simulator_log.close()
        return

    def run_cli(self, conf: Artifact) -> None:
        self.status.step_id = conf.step_id
        workdir = conf.get_workdir()
        out_path = '{}/cli_out.csv'.format(workdir)
        conf_path = conf.path

        with open(out_path, 'w') as f:
            """
            Run SIMBAD-CLI binary with configuration as argument, and pipe stdout to cli_out.csv file
            Periodically update runtime info with psutil. 
            """
            cli_out = open(out_path, "a")
            process = subprocess.Popen((self.executable_path, conf_path, out_path), stdout=cli_out,
                                       stderr=subprocess.PIPE)

            progress = threading.Thread(target=self.update_progress, args=[workdir, process])
            progress.start()
            progress.join()
            cli_out.close()

        end_timestamp = datetime.datetime.utcnow()

        self.result = Artifact(
            created_utc=end_timestamp,
            size_kb=os.path.getsize(out_path),
            path=out_path,
            name='cli_out',
            step_id=conf.step_id,
            simulation_id=conf.simulation_id,
            file_type='CSV'
        )
        log_path = workdir + '/logs/simulator.log'

        # self.log = Artifact(
        #     created_utc=end_timestamp,
        #     size_kb=os.path.getsize(log_path),
        #     path=log_path,
        #     name='simulator.log',
        #     step_id=conf.step_id,
        #     simulation_id=conf.simulation_id,
        #     file_type='LOG'
        # )
        self.is_finished = True
        return
