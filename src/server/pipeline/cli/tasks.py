import datetime
import enum
import logging

from celery import Celery
from time import sleep

from config.settings import SIMBAD_CLI_BINARY_PATH, SIMBAD_CLI_EXECUTOR, POLLING_PERIOD
from database import db_session
from models.simulation_step import SimulationStep
from models.cli_runtime_info import CliRuntimeInfo
from models.artifact import Artifact
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
    """
    Returns task executor for cli step, specified by SIMBAD_CLI_EXECUTOR env variable
    :return:
    """
    return {
        ExecutorType.LOCAL: get_local_cli_executor(),
        ExecutorType.HTTP: get_local_cli_executor(),
        ExecutorType.SSH: get_local_cli_executor()
    }.get(ExecutorType[SIMBAD_CLI_EXECUTOR])


@celery.task(bind=True, name='SIMBAD-CLI')
def cli_step(self, artifact_id: int) -> int:
    """
    Celery task for generating CLI output from configuration.
    Ideally, here I'd like to be able to pass Artifact object, so I don't need to get it from database
    but due to the way that serializers in celery work, it is not possible. If passed, the Artifact object
    would be serialized to list of its properties: ['id', 'created_utc', 'size_kb', 'path']. The proper
    way to do it would be to set celery serializer to already used in flask AlchemyEncoder
    see:
        - https://stackoverflow.com/questions/21631878/celery-is-there-a-way-to-write-custom-json-encoder-decoder

    :param artifact_id:
    :param self:
    :return: the id of created cli artifact
    """
    conf: Artifact = db_session.query(Artifact).get(artifact_id)
    step: SimulationStep = db_session.query(SimulationStep).get(conf.step_id)
    step.celery_id = self.request.id
    step.status = 'ONGOING'
    db_session.begin()
    runtime_info: CliRuntimeInfo = CliRuntimeInfo(
        memory=0,
        cpu=0,
        step_id=step.id
    )
    db_session.add(runtime_info)
    db_session.commit()

    executor: BaseExecutor = get_cli_executor()
    executor.execute(conf)

    while executor.is_finished is not True:
        # Setting runtime_info like: runtime_info = executor.status seems to cause executor info not updating in
        # SimulationStep, when querying @simulation_api.route('/step/<step_id>') endpoint
        # TODO - find out whether step id is assigned incorrectly to configuration Artifact, or assigning another
        #  sqlalchemy object to runtime_info overrides some internal property that should not be overridden
        #  (ex. _sa_instance_state)
        db_session.begin()
        runtime_info.cpu = executor.status.cpu
        runtime_info.memory = executor.status.memory
        runtime_info.progress = executor.status.progress
        db_session.commit()
        sleep(POLLING_PERIOD)

    db_session.begin()
    result: Artifact = executor.result
    result.simulation_id = step.simulation_id
    step.finished_utc = datetime.datetime.utcnow()
    step.status = 'SUCCESS'
    runtime_info.memory = 0
    runtime_info.cpu = 0
    runtime_info.progress = 100
    db_session.add(result)
    db_session.commit()

    return result.id
