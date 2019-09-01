import datetime
import logging
import os
import subprocess
import time

import psutil as psutil
from celery import Celery, chain

from server.config.constants import CLI_PATH
from server.pipeline.setup.workdir_setup import simulation_workdir_setup

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


@celery.task(bind=True, name='Cli step 1')
def cli_step(self, req_json):
    logger.info('Different file cli task')
    timestamp = datetime.datetime.now()
    name = req_json['configurationName']
    conf = req_json['configuration']
    work_dir = simulation_workdir_setup(conf, name)
    conf_path = '{}/{}'.format(work_dir, name + '.json')

    command = (CLI_PATH, conf_path)
    out_path = '{}/cli_out.csv'.format(work_dir)

    with open(out_path, 'w') as f:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        process_info = psutil.Process(process.pid)
        counter = 0
        start = time.time()
        for c in iter(lambda: process.stdout.read(1), b''):
            counter += 1
            if counter % 100000 == 0:
                worker_info = {
                    "cpu": process_info.cpu_percent(),
                    "memory": process_info.memory_info().rss / 1000000,
                    "uptime": time.time() - start,
                }
                self.update_state(state='PROGRESS', meta={"workerInfo": worker_info, "startTimestamp": timestamp})
            line = c.decode('utf-8')
            f.write(line)

    result = {
        "time": time.time() - start,
        "artifactPath": out_path,
        "artifactSize:": os.path.getsize(out_path) / 1000000
    }

    return result

