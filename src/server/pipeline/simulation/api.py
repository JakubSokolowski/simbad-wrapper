import datetime
import json

import celery.worker.control
from celery.result import AsyncResult
from flask import Blueprint, jsonify, request, url_for

from database import engine, db_session
from models.encoder import AlchemyEncoder
from models.product import Product
from models.simulation import Simulation, Step
from server.pipeline.setup.workdir_setup import setup_workdir
from server.pipeline.util.request import request_to_json
from .tasks import run_simulation


simulation_api = Blueprint('simulation_api', __name__)


@simulation_api.route('/simulation/run', methods=['POST'])
def run():
    request_data: dict = request_to_json(request)
    paths = setup_workdir(request_data)
    task = run_simulation.delay(request_data)
    return jsonify({"taskId": task.id}), 202, {'Location': url_for('simulation_api.status', task_id=task.id)}


def get_current_simulation() -> Simulation:
    return db_session.query(Simulation).filter(
        Simulation.started_utc is not None and Simulation.finished_utc is None
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
        return jsonify({"status": "IDLE"})


@simulation_api.route('/cli/status')
def cli_status():
    return jsonify({"hehe": "xd"})


@simulation_api.route('/testdb')
def index():
    product = db_session.query(Product).all()
    return json.dumps(product, cls=AlchemyEncoder)


@simulation_api.route('/add', methods=['POST'])
def add():
    product = Product(name='Crack2')
    simulation = Simulation(
        started_utc=datetime.datetime.now(),
        name="test_simulation",
        current_step=Step.CONF
    )
    db_session.begin()
    db_session.add(simulation)
    db_session.commit()
    return jsonify({"status": "OK"})


def unpack_chain(nodes):
    while nodes.parent:
        yield nodes.parent
        nodes = nodes.parent
    yield nodes


def store(node):
    id_chain = []
    while node.parent:
        id_chain.append(node.id)
        node = node.parent
    id_chain.append(node.id)
    return id_chain


def restore(id_chain):
    id_chain.reverse()
    last_result = None
    for tid in id_chain:
        result = AsyncResult(tid)
        result.parent = last_result
        last_result = result
    return last_result


@simulation_api.route('/simulation/tasks/<task_id>', methods=['GET', 'DELETE'])
def job_status(task_id: str):
    """
    Returns current status of cli_step celery task represented by its id
    :param task_id: celery id of cli_step task
    :return: current task status
    """
    task: AsyncResult = run_simulation.AsyncResult(task_id)
    print('Simulation task id', task_id)
    print('Simulation task name', task.name)
    first_children = list(map(lambda x: x.id, task.children))
    first_task = run_simulation.AsyncResult(first_children[0])
    print('Chain result', task.result)
    print('First subtask result', first_task.result)
    second_task = run_simulation.AsyncResult(first_task.children[0].id)
    print('Second subtask result', second_task.result)
    print('task cache', task._cache)

    if request.method == 'DELETE':
        celery.worker.control.revoke(task_id, terminate=True)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'PENDING',
            'info': task.info
        }
    elif task.state != 'FAILURE':
        print(task.children)
        print('Chain results', [t.result for t in list(unpack_chain(task))])
        print('Children Results', list(map(lambda x: x.result, task.children)))
        response = {
            'state': task.state,
            'info': task.info,
            'parent': task.parent,
            'first_info': run_simulation.AsyncResult(task.result[0][0]).info,
            'first_result': run_simulation.AsyncResult(task.result[0][0]).result,
            'second_id': task.result[0][1][0][0],
            'second_info': run_simulation.AsyncResult(task.result[0][1][0][0]).info,
            'second_result': run_simulation.AsyncResult(task.result[0][1][0][0]).result,
            'tuple': task.as_tuple(),
            'task_id': task.task_id,
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
            response['status'] = 'COMPLETED'
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)
