import datetime
import json
import os

from config.settings import SIMBAD_DATA_PATH
from database import db_session
from models.simulation import Simulation, Step, Artifact, SimulationStep


def get_conf_name(name: str) -> str:
    if name.endswith('.json'):
        return name
    return name + '.json'


def create_workdir(conf_name: str, simulation_id: int) -> str:
    """
    Creates new dir for simulation in SIMBAD_DATA_PATH
    :param conf_name:
    :param simulation_id:
    :return: path to created workdir
    """
    work_dir_path = SIMBAD_DATA_PATH + '/SIM_{}_CONF_{}'.format(simulation_id, conf_name)
    if not os.path.exists(work_dir_path):
        os.mkdir(work_dir_path)

    return work_dir_path


def setup_workdir(request_data: dict) -> Artifact:
    """
    Creates new dir for simulation and places simulation configuration file in it
    :param request_data: Flask request with configuration
    :return: tuple with path to workdir and saved configuration
    """
    conf_name = get_conf_name(request_data['configurationName'])
    conf = request_data['configuration']

    start_time = datetime.datetime.utcnow()

    simulation = Simulation(started_utc=start_time, name="test_simulation", current_step=Step.CONF)
    db_session.add(simulation)
    db_session.flush()
    step = SimulationStep(started_utc=start_time, origin=Step.CONF, simulation_id=simulation.id)
    db_session.add(step)
    db_session.flush()

    workdir_path = create_workdir(conf_name, simulation.id)
    conf_path = '{}/{}'.format(workdir_path, conf_name)

    simulation.workdir = workdir_path

    with open(conf_path, 'w+') as f:
        json.dump(conf, f, indent=2)

    configuration = Artifact(
        size_kb=os.path.getsize(conf_path) << 10,
        path=conf_path,
        created_utc=start_time,
        step_id=step.id,
        simulation_id=simulation.id
    )
    simulation.artifacts.append(configuration)
    step.artifacts.append(configuration)
    simulation.steps.append(step)

    db_session.begin()
    db_session.add_all([configuration, step, simulation])
    db_session.flush()
    db_session.commit()

    return configuration


