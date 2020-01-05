import datetime
import os
import subprocess
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

    def update_progress(self, process: subprocess.Popen):
        for line in iter(lambda: process.stderr.readline(), b''):
            curr, target = line.decode('utf8').split('/')
            self.status.progress = int(float(int(curr) / int(target)) * 100.0)

    def update_runtime(self, out_path: str, process: subprocess.Popen):
        counter = 0
        process_info = psutil.Process(process.pid)
        with open(out_path, 'w') as f:
            for c in iter(lambda: process.stdout.read(1), b''):
                counter += 1

                if counter % 1000000 == 0:
                    # Not sure if that byte conversion is right,
                    # almost sure that it is not
                    memory = process_info.memory_info().rss / 1000000
                    cpu = process_info.cpu_percent()
                    self.status.memory = memory
                    self.status.cpu = cpu

                line = c.decode('utf-8')
                f.write(line)

    def run_cli(self, conf: Artifact) -> None:
        self.status.step_id = conf.step_id
        out_path = '{}/cli_out.csv'.format(conf.get_workdir())
        conf_path = conf.path

        with open(out_path, 'w') as f:
            """
            Run SIMBAD-CLI binary with configuration as argument, and pipe stdout to cli_out.csv file
            Periodically update runtime info with psutil. 
            Passing the stdout to some file like : /path/to/cli /path/to/conf < /out/path
            does not seem to work, so the workaround is to pipe stdout and stderr to script, 
            and manually write the stdout fo file.
            TODO: find out whether there is such option i Popen that would allow pipe stdout from SIMBAD-CLI
            to some file from the cmd level
            """
            process = subprocess.Popen((self.executable_path, conf_path, out_path), stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process_info = psutil.Process(process.pid)
            counter = 0

            progress = threading.Thread(target=self.update_progress, args=[process])
            runtime = threading.Thread(target=self.update_runtime, args=[out_path, process])

            progress.start()
            runtime.start()
            progress.join()
            runtime.join()

            for c in iter(lambda: process.stdout.read(1), b''):
                counter += 1

                if counter % 1000000 == 0:
                    memory = process_info.memory_info().rss / 1000000
                    cpu = process_info.cpu_percent()
                    self.status.memory = memory
                    self.status.cpu = cpu

                line = c.decode('utf-8')
                f.write(line)

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
        self.is_finished = True
        return
