import datetime
import enum
import logging
from time import sleep
from typing import List

from celery import Celery
from sshtunnel import SSHTunnelForwarder

import config.settings as settings
from database import db_session
from models.simulation import Artifact, SimulationStep, AnalyzerRuntimeInfo
from server.executors import BaseExecutor
from server.pipeline.analyzer.analyzer_http_executor import AnalyzerHttpExecutor
from server.pipeline.analyzer.analyzer_ssh_executor import AnalyzerSshExecutor

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


class ExecutorType(enum.Enum):
    LOCAL = 'LOCAL',
    HTTP = 'HTTP',
    SSH = 'SSH'


def get_http_analyzer_executor() -> AnalyzerHttpExecutor:
    return AnalyzerHttpExecutor(
        start_endpoint=settings.SIMBAD_ANALYZER_START_ENDPOINT,
        status_endpoint=settings.SIMBAD_ANALYZER_STATUS_ENDPOINT,
        runtime_endpoint=settings.SIMBAD_ANALYZER_RUNTIME_ENDPOINT,
        result_endpoint=settings.SIMBAD_ANALYZER_RESULT_ENDPOINT,
    )


def get_analyzer_ssh_executor() -> AnalyzerSshExecutor:
    tunnel = SSHTunnelForwarder(
        (settings.SIMBAD_ANALYZER_HOST, 22),
        ssh_username=settings.SIMBAD_ANALYZER_USER,
        ssh_password=settings.SIMBAD_ANALYZER_PASSWORD,
        local_bind_address=('127.0.0.1', settings.SIMBAD_ANALYZER_LOCAL_PORT),
        remote_bind_address=('127.0.0.1', settings.SIMBAD_ANALYZER_LOCAL_PORT)

    )

    return AnalyzerSshExecutor(
        start_endpoint=settings.SIMBAD_ANALYZER_START_ENDPOINT,
        status_endpoint=settings.SIMBAD_ANALYZER_STATUS_ENDPOINT,
        runtime_endpoint=settings.SIMBAD_ANALYZER_RUNTIME_ENDPOINT,
        result_endpoint=settings.SIMBAD_ANALYZER_RESULT_ENDPOINT,
        tunnel=tunnel
    )


def get_analyzer_executor():
    """
    Returns task executor for cli step, specified by SIMBAD_CLI_EXECUTOR env variable
    :return:
    """
    return {
        ExecutorType.HTTP: get_http_analyzer_executor(),
        ExecutorType.SSH: get_analyzer_ssh_executor()
    }.get(ExecutorType[settings.SIMBAD_CLI_EXECUTOR])


@celery.task(bind=True, name='SIMBAD-ANALYZER')
def analyzer_task(self, artifact_id: int) -> List[(int, str)]:
    cli_out: Artifact = db_session.query(Artifact).get(artifact_id)
    step = db_session.query(SimulationStep).get(cli_out.simulation_id)
    step.celery_id = self.request.id
    db_session.begin()

    runtime_info: AnalyzerRuntimeInfo = AnalyzerRuntimeInfo(
        progress=0,
        step_id=step.id
    )
    db_session.add(runtime_info)
    db_session.commit()

    executor: BaseExecutor = get_analyzer_executor()
    executor.execute(cli_out)

    while executor.is_finished is not True:
        db_session.begin()
        runtime_info.progress = executor.status.progress
        db_session.commit()
        sleep(settings.SIMBAD_ANALYZER_POLLING_PERIOD)

    db_session.begin()
    result: List[Artifact] = executor.result
    step.finished_utc = datetime.datetime.utcnow()
    runtime_info.progress = 100
    db_session.add_all(result)
    db_session.commit()

    return list(map(lambda artifact: (artifact.id, artifact.path), result))
