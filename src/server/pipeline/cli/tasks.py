import datetime
import enum
import logging
from time import sleep

from celery import Celery
from flask import jsonify

from config.settings import SIMBAD_CLI_BINARY_PATH, SIMBAD_CLI_EXECUTOR, POLLING_PERIOD
from database import db_session
from models.simulation import ArtifactModel, SimulationStepModel, CliRuntimeInfoModel, Artifact
from server.executors import BaseExecutor
from server.pipeline.cli.cli_local_executor import CliLocalExecutor

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


class ExecutorType(enum.Enum):
    LOCAL = 'LOCAL',
    HTTP = 'HTTP',
    SSH = 'SSH'


def get_local_cli_executor():
    return CliLocalExecutor(SIMBAD_CLI_BINARY_PATH)


def get_cli_executor():
    return {
        ExecutorType.LOCAL: get_local_cli_executor(),
        ExecutorType.HTTP: get_local_cli_executor(),
        ExecutorType.SSH: get_local_cli_executor()
    }.get(ExecutorType[SIMBAD_CLI_EXECUTOR])


@celery.task(bind=True, name='SIMBAD-CLI')
def cli_step(self, conf: Artifact) -> Artifact:
    """
    Celery task for generating CLI output from configuration
    :param conf:
    :param self:
    :return: Artifact object representing CLI output
    """
    db_session.begin()
    step = db_session.query(SimulationStepModel).get(conf.simulation_id)
    step.celery_id = self.request.id
    runtime_info: CliRuntimeInfoModel = CliRuntimeInfoModel(
        memory=0,
        cpu=0,
        step_id=step.id
    )
    db_session.add(runtime_info)
    db_session.commit()

    executor: BaseExecutor = get_cli_executor()
    executor.execute(conf.id)

    while executor.is_finished is not True:
        db_session.begin()
        runtime_info = executor.get_status()
        db_session.commit()
        sleep(POLLING_PERIOD)

    db_session.begin()
    result: Artifact = executor.get_result()
    step.finished_utc = datetime.datetime.utcnow()
    runtime_info.memory = 0
    runtime_info.cpu = 0
    db_session.add(result)
    db_session.commit()

    return result
