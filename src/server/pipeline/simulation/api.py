from flask import Blueprint, jsonify, request
from sqlalchemy import and_

from database import db_session
from models.artifact import Artifact
from models.simulation import Simulation
from models.simulation_step import SimulationStep
from server.pipeline.setup.workdir_setup import setup_workdir
from server.pipeline.util.request import request_to_json
from .tasks import run_simulation

simulation_api = Blueprint('simulation_api', __name__)


@simulation_api.route('/start', methods=['POST'])
def start():
    request_data: dict = request_to_json(request)
    conf: Artifact = setup_workdir(request_data)
    db_session.begin()
    db_session.flush()
    step = db_session.query(SimulationStep).get(conf.step_id)
    task = run_simulation.delay(conf.id)
    step.celery_id = task.id
    db_session.commit()
    return jsonify(step)


def get_current_simulation() -> Simulation:
    return db_session.query(Simulation).filter(
        Simulation.started_utc is not None and Simulation.finished_utc is None
    ).first()


@simulation_api.route('/status')
def current_simulation_status():
    simulation = get_current_simulation()
    if simulation is not None:
        return jsonify({
            "status": 'BUSY',
            "currentStep": simulation.current_step,
            "simulationId": simulation.id
        })
    else:
        return jsonify({"status": "IDLE"})


@simulation_api.route('/latest')
def get_latest_simulation():
    simulation = db_session.query(Simulation).order_by(Simulation.id.desc()).first()
    if simulation is not None:
        return jsonify(simulation)
    return "FAILED"


@simulation_api.route('/status/<simulation_id>')
def simulation_status(simulation_id):
    simulation = db_session.query(Simulation).get(simulation_id)
    if simulation is not None:
        return jsonify(simulation)
    return "Simulation not found"


@simulation_api.route('/step/<step_id>')
def step_status(step_id):
    step = db_session.query(SimulationStep).get(step_id)
    if step is not None:
        return jsonify(step)
    return "Simulation step not found"


@simulation_api.route('/range/latest')
def get_simulation_in_range_latest():
    numSimulations = request.args.get('num', default=10, type=int)
    simulations = db_session.query(Simulation).order_by(
        Simulation.id.desc()).limit(numSimulations).all()
    simple_simulations = list(map(lambda sim: to_simple_simulation_info(sim), simulations))
    return jsonify(simple_simulations)


@simulation_api.route('/range/chunk')
def get_simulation_in_range_chunk():
    simulationId = request.args.get('id', default=1000, type=int)
    numSimulations = request.args.get('num', default=10, type=int)
    simulations = db_session.query(SimulationStep).filter(
        Simulation.id > simulationId).limit(numSimulations).all()
    return jsonify(simulations)


@simulation_api.route('/range/date')
def get_simulation_in_range_date(date_from, date_to):
    simulations = db_session.query(SimulationStep).filter(
        Simulation.started_utc.between(date_from, date_to))
    simple_simulations = list(map(lambda sim: to_simple_simulation_info(sim), simulations))
    return jsonify(simple_simulations)


def to_simple_simulation_info(simulation: Simulation):
    simple_info = {
        "simulationId": simulation.id,
        "startedUtc": simulation.started_utc,
        "finishedUtc": simulation.finished_utc,
        "configuration": get_configuration(simulation),
        "reportId": get_report_id(simulation),
        "cli": get_cli_status(simulation),
        "analyzer": get_analyzer_status(simulation),
        "reports": get_reports_status(simulation),
        "status": simulation.status
    }
    return simple_info


def get_report_id(simulation: Simulation):
    report: Artifact = db_session.query(Artifact).filter(
        and_(Artifact.simulation_id == simulation.id, Artifact.file_type == 'PDF')
    ).first()
    return None if report is None else report.id


def get_configuration(simulation: Simulation):
    configuration: Artifact = db_session.query(Artifact).filter(
        and_(Artifact.simulation_id == simulation.id, Artifact.file_type == 'JSON')
    ).first()
    return {"name": configuration.name, "id": configuration.id}


def get_cli_status(simulation):
    step: SimulationStep = db_session.query(SimulationStep).filter(
        and_(SimulationStep.simulation_id == simulation.id, SimulationStep.origin == 'CLI')
    ).first()
    if step is not None:
        progress = step.cli_runtime_info.progress
        return {"status": step.status, "progress": progress}
    return None


def get_analyzer_status(simulation):
    step: SimulationStep = db_session.query(SimulationStep).filter(
        and_(SimulationStep.simulation_id == simulation.id, SimulationStep.origin == 'ANALYZER')
    ).first()
    if step is not None:
        progress = step.analyzer_runtime_info.progress
        return {"status": step.status, "progress": progress}
    return None


def get_reports_status(simulation):
    step: SimulationStep = db_session.query(SimulationStep).filter(
        and_(SimulationStep.simulation_id == simulation.id, SimulationStep.origin == 'REPORT')
    ).first()
    if step is not None:
        return {"status": step.status, "progress": 100}
    return None
