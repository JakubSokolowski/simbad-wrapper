import logging

from flask import jsonify, Blueprint

from server.pipeline import demo_tasks

demo_api = Blueprint('tasks', __name__)
logger = logging.getLogger()


@demo_api.route('/')
def view_base():
    return jsonify({'status': 'success'})


@demo_api.route('/sleep/', methods=['POST'])
@demo_api.route('/sleep/<int:sleep_time>', methods=['POST'])
def view_start_task(sleep_time=5):
    """start task, return task_id"""

    logger.info('start task...')
    task = demo_tasks.wait_task.apply_async(kwargs={'sleep_time': sleep_time})

    logger.info('return task...')
    return jsonify({
        'task_id': task.id,
        'state': task.state,
        'sleep_time': sleep_time
    }), 202


@demo_api.route('/sleep/<task_id>', methods=['GET'])
def view_check_task(task_id):
    """return task state"""

    task = demo_tasks.wait_task.AsyncResult(task_id)
    output = {'task_id': task.id, 'state': task.state}
    if task.state == 'SUCCESS':
        output.update({'result': task.result})
    return jsonify(output)
