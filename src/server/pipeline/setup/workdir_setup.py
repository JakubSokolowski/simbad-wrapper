import datetime
import json
import os

from config.settings import SIMBAD_DATA_PATH
from database import db_session
from models.artifact import Artifact
from models.simulation import Simulation
from models.simulation_step import SimulationStep


def get_conf_name(name: str) -> str:
    if name.endswith('.json'):
        return name
    return name + '.json'


def create_workdir(simulation_id: int) -> str:
    """
    Creates new dir for simulation in SIMBAD_DATA_PATH
    :param simulation_id:
    :return: path to created workdir
    """
    work_dir_path = os.path.join(SIMBAD_DATA_PATH, 'SIM_{}'.format(simulation_id))
    logs_path = os.path.join(work_dir_path, 'logs')
    if not os.path.exists(work_dir_path):
        os.mkdir(work_dir_path)
    if not os.path.exists(logs_path):
        os.mkdir(logs_path)

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

    simulation = Simulation(started_utc=start_time, name="test_simulation", current_step="CLI")
    db_session.add(simulation)
    db_session.flush()
    step = SimulationStep(started_utc=start_time, origin="CLI", simulation_id=simulation.id, status='ONGOING')
    db_session.add(step)
    db_session.flush()

    workdir_path = create_workdir(simulation.id)
    conf_path = '{}/{}'.format(workdir_path, conf_name)

    simulation.workdir = workdir_path
    simulation.current_step_id = step.id

    with open(conf_path, 'w+') as f:
        json.dump(conf, f, indent=2)

    configuration = Artifact(
        size_kb=os.path.getsize(conf_path),
        path=conf_path,
        created_utc=start_time,
        step_id=step.id,
        name=conf_name,
        file_type='JSON',
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


