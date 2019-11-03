import datetime
import logging
import os
import subprocess

import psutil as psutil
from celery import Celery

from database import db_session
from models.simulation import Artifact, SimulationStep, CliRuntimeInfo

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


@celery.task(bind=True, name='SIMBAD-CLI')
def cli_step(self, paths: (int, str, str)) -> Artifact:
    """
    Celery task for generating CLI output from configuration
    :param self:
    :param paths:
    :return:
    """
    db_session.begin()
    step = db_session.query(SimulationStep).get(paths[0])
    step.celery_id = self.request.id
    runtime_info: CliRuntimeInfo = CliRuntimeInfo(
        memory=0,
        cpu=0,
        step_id=step.id
    )
    db_session.add(runtime_info)
    db_session.commit()

    out_path = '{}/cli_out.csv'.format(paths[1])

    with open(out_path, 'w') as f:
        process = subprocess.Popen(('/home/jakub/dev/uni/simbad/data/bin/simbad-cli', paths[2]), stdout=subprocess.PIPE)
        process_info = psutil.Process(process.pid)
        counter = 0
        for c in iter(lambda: process.stdout.read(1), b''):
            counter += 1
            if counter % 1000000 == 0:
                db_session.begin()
                memory = process_info.memory_info().rss / 1000000
                cpu = process_info.cpu_percent()
                runtime_info.memory = memory
                runtime_info.cpu = cpu
                print('Updating info', memory, cpu)
                db_session.commit()

            line = c.decode('utf-8')
            f.write(line)

    end_timestamp = datetime.datetime.utcnow()

    result = Artifact(
        created_utc=end_timestamp,
        size_kb=os.path.getsize(out_path),
        path=out_path,
        step_id=step.id
    )

    db_session.begin()
    step.finished_utc = end_timestamp
    runtime_info.memory = 0
    runtime_info.cpu = 0
    db_session.add(result)
    db_session.commit()

    return result
