import sys

from flask import Blueprint, jsonify, request

from database import db_session
from models.simulation import SimulationModel, SimulationStepModel, ArtifactModel, Artifact
from server.pipeline.setup.workdir_setup import setup_workdir
from server.pipeline.util.request import request_to_json
from .tasks import run_simulation

simulation_api = Blueprint('simulation_api', __name__)


@simulation_api.route('/simulation/start', methods=['POST'])
def run():
    request_data: dict = request_to_json(request)
    conf: Artifact = setup_workdir(request_data)
    print('conf', conf)
    db_session.begin()
    step = db_session.query(SimulationStepModel).get(conf.step_id)
    task = run_simulation.delay(conf)
    step.celery_id = task.id
    db_session.commit()
    return jsonify(step)


def get_current_simulation() -> SimulationModel:
    return db_session.query(SimulationModel).filter(
        SimulationModel.started_utc is not None and SimulationModel.finished_utc is None
    ).first()


@simulation_api.route('/simulation/status')
def simulation_status():
    simulation = get_current_simulation()
    if simulation is not None:
        return jsonify({
            "status": 'BUSY',
            "currentStep": simulation.current_step,
            "simulationId": simulation.id
        })
    else:
        return jsonify({"status": "IDLE"},)


@simulation_api.route('/step/<step_id>')
def step_status(step_id):
    step = db_session.query(SimulationStepModel).get(step_id)
    if step is not None:
        return jsonify(step)
    return 404
