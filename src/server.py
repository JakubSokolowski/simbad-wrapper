import os
import subprocess
import time

import psutil
from celery import Celery
from flask import Flask, request, jsonify, url_for
from flask_cors import CORS

from env.constants import CLI_PATH
from pipeline.setup import request_to_json, simulation_workdir_setup

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

cli_status = {
    'status': 'IDLE',
    'taskID': None
}


def reset_cli_status():
    global cli_status
    cli_status = {
        'status': 'IDLE',
        'taskID': None
    }
    return


def set_cli_status(task_id):
    global cli_status
    cli_status = {
        'status': 'BUSY',
        'taskID': task_id
    }
    return


@app.route('/api/cli/status')
def status():
    global cli_status
    return jsonify(cli_status)


@celery.task(bind=True)
def simulation(self, req_json):
    print(req_json)
    name = req_json['configurationName']
    conf = req_json['configuration']
    work_dir = simulation_workdir_setup(conf, name)
    conf_path = '{}/{}'.format(work_dir, name + '.json')

    command = (CLI_PATH, conf_path)
    out_path = '{}/cli_out.csv'.format(work_dir)
    worker_info = {}

    with open(out_path, 'w') as f:
        process = subprocess.Popen(command, stdout=subprocess.PIPE)
        process_info = psutil.Process(process.pid)
        counter = 0
        start = time.time()
        for c in iter(lambda: process.stdout.read(1), b''):
            counter += 1
            if counter % 100000 == 0:
                worker_info = {
                    "cpu": process_info.cpu_percent(),
                    "memory": process_info.memory_info().rss / 1000000,
                    "uptime": time.time() - start,
                }
                self.update_state(state='PROGRESS', meta={"workerInfo": worker_info})
            line = c.decode('utf-8')
            f.write(line)

    result = {
        "time": time.time() - start,
        "artifactPath": out_path,
        "artifactSize:": os.path.getsize(out_path) / 1000000
    }

    reset_cli_status()

    return {"result": result, "workerInfo": worker_info}


@app.route('/api/cli/status/<task_id>')
def task_status(task_id):
    task = simulation.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'PENDING',
            'info': task.info
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('RUNNING'),
            'cliInfo': task.info.get('workerInfo', {})
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


@app.route('/api/cli/run', methods=['POST'])
def run_simulation():
    req_json = request_to_json(request)
    task = simulation.delay(req_json=req_json)
    set_cli_status(task.id)
    return jsonify({"id": task.id}), 202, {'Location': url_for('status', task_id=task.id)}


if __name__ == '__main__':
    app.run(port=8000, debug=True)
