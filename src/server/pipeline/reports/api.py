from flask import Blueprint, jsonify, request

from database import db_session
from models.simulation import Simulation, SimulationStep, Artifact
from server.pipeline.reports.tasks import reports_step
reports_api = Blueprint('reports_api', __name__)


@reports_api.route('/latest', methods=['GET'])
def generate_reports():
    simulation = db_session.query(Simulation).order_by(Simulation.id.desc()).first()
    if simulation is not None:
        reports_step.delay(simulation.id)
        return "OK"
    return "FAILED"
