import logging
import time

from celery import Celery, chain
from celery.result import AsyncResult

from server.pipeline.analyzer.tasks import analyzer_step
from server.pipeline.cli.tasks import cli_step
from server.pipeline.reports.tasks import reports_step

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


@celery.task(bind=True, trail=True, name='Simulation')
def run_simulation(self, artifact_id) -> AsyncResult:
    """

    :param self:
    :param artifact_id:
    :return:
    """
    result = chain(
        cli_step.s(artifact_id),
        analyzer_step.s(),
        reports_step.s()
    ).apply_async()
    return result
