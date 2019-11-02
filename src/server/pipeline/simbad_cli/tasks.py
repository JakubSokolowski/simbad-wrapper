import datetime
import logging
import os
import subprocess

import psutil as psutil
import time
from celery import Celery

from database import db_session
from models.simulation import Artifact, SimulationStep, Step, Simulation

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


@celery.task(bind=True, name='SIMBAD-CLI')
def cli_step(self, paths: (str, str), simulation_id: int) -> Artifact:
    logger.info('Different file cli task')
    start_timestamp = datetime.datetime.now()

    step = SimulationStep(
        simulation_id=simulation_id,
        started_utc=start_timestamp,
        origin=Step.CLI,
    )

    db_session.query(Simulation).filter(Simulation.id == simulation_id).update({'current_step': Step.CLI})
    db_session.begin()
    db_session.add(step)
    db_session.commit()

    command = ('simbad-cli', paths[0])
    out_path = '{}/cli_out.csv'.format(paths[1])

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
                self.update_state(state='PROGRESS', meta={"workerInfo": worker_info, "startTimestamp": start_timestamp})
            line = c.decode('utf-8')
            f.write(line)

    end_timestamp = datetime.datetime.now()

    result = Artifact(
        created_utc=end_timestamp,
        size_kb=os.path.getsize(out_path) << 10,
        path=out_path,
        simulation_id=simulation_id,
        step=step
    )

    db_session.begin()
    db_session.add(step)
    db_session.commit()

    return result
