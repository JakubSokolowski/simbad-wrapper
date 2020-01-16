from flask import Blueprint, jsonify, request

from database import db_session
from models.simulation import Simulation
from models.simulation_step import SimulationStep
from models.artifact import Artifact
from server.pipeline.reports.tasks import reports_step, build_cell_model

reports_api = Blueprint('reports_api', __name__)


@reports_api.route('/latest', methods=['GET'])
def generate_reports():
    simulation = db_session.query(Simulation).order_by(Simulation.id.desc()).first()
    if simulation is not None:
        reports_step.delay(simulation.id)
        return "OK"
    return "FAILED"


@reports_api.route('/model', methods=['GET'])
def generate_model():
    simulation = db_session.query(Simulation).order_by(Simulation.id.desc()).first()
    if simulation is not None:
        build_cell_model.delay(simulation.workdir)
        return "OK"
    return "FAILED"
