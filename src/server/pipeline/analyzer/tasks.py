import datetime
import enum
import logging
import os
from time import sleep
from typing import List

from celery import Celery
from sshtunnel import SSHTunnelForwarder

import config.settings as settings
from database import db_session
from models.analyzer_runtime_info import AnalyzerRuntimeInfo
from models.artifact import Artifact
from models.simulation import Simulation
from models.simulation_step import SimulationStep
from server.artifacts.utils import path_leaf, file_extension
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
        local_bind_address=('127.0.0.1', int(settings.SIMBAD_ANALYZER_PORT)),
        remote_bind_address=('127.0.0.1', int(settings.SIMBAD_ANALYZER_PORT))

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
    }.get(ExecutorType[settings.SIMBAD_ANALYZER_EXECUTOR])


@celery.task(bind=True, name='SIMBAD-ANALYZER')
def analyzer_step(self, artifact_id: int) -> int:
    print('analyzer artifact id', artifact_id)
    cli_out: Artifact = db_session.query(Artifact).get(artifact_id)
    print('analyzer artifact id', cli_out.__dict__)

    simulation: Simulation = db_session.query(Simulation).get(cli_out.simulation_id)
    start_time = datetime.datetime.utcnow()
    step: SimulationStep = SimulationStep(started_utc=start_time, origin="ANALYZER", simulation_id=simulation.id,
                                          status='ONGOING')
    db_session.flush()
    step.celery_id = self.request.id
    simulation.steps.append(step)
    simulation.current_step = "ANALYZER"
    simulation.current_step_id = step.id

    db_session.begin()
    db_session.add_all([simulation, step])
    db_session.commit()

    db_session.begin()
    runtime_info: AnalyzerRuntimeInfo = AnalyzerRuntimeInfo(
        progress=0,
        is_finished=False,
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
    print(executor.result)
    result: List[Artifact] = list(map(lambda path: Artifact(path=path), executor.result))

    for artifact in result:
        artifact.step_id = step.id
        artifact.name = path_leaf(artifact.path)
        artifact.file_type = file_extension(artifact.path)
        artifact.created_utc = datetime.datetime.fromtimestamp(os.path.getmtime(artifact.path))
        artifact.simulation_id = step.simulation_id
        artifact.size_kb = os.path.getsize(artifact.path)

    step.finished_utc = datetime.datetime.utcnow()
    step.status = 'SUCCESS'
    runtime_info.progress = 100
    db_session.add_all(result)
    db_session.commit()

    return simulation.id
