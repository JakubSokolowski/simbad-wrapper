import datetime
import logging
import time

from celery import Celery, chain
from celery.result import AsyncResult

from server.pipeline.simbad_cli.tasks import cli_step

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


@celery.task(bind=True, trail=True, name='Simulation')
def run_simulation(self, paths: (int, str, str)) -> AsyncResult:
    result = chain(
        cli_step.s(paths)
    )()
    return result


@celery.task(bind=True, name='Cli step 2')
def cli_step_2(self, req_json):
    logger.info('Same file cli_step task')
    time.sleep(5)
    info = {
        'step': 'cli_step_2',
        'stats': 'ayy'
    }
    self.update_state(state='PROGRESS', meta={'info': info})
    time.sleep(10)
    info = {
        'step': 'cli_step_2',
        'stats': 'ayyy ayyy'
    }
    return {'result': 'cli_step_2_result'}



