import json
import os

from server.config.constants import OUT_PATH

current_id = 0


def request_to_json(req):
    print(req)
    return json.loads(req.data.decode('utf8'))


def get_available_dir_name(name) -> str:
    id = 0
    work_dir = OUT_PATH + '/SIM_{}_CONF_{}'.format(current_id, name)
    if os.path.exists(work_dir):
        newId = int(work_dir.split('_')[1]) + 1


def simulation_workdir_setup(conf, name) -> str:
    print('directory setup')
    global current_id
    work_dir = OUT_PATH + '/SIM_{}_CONF_{}'.format(current_id, name)
    os.mkdir(work_dir)
    current_id += 1
    with open('{}/{}'.format(work_dir, name + '.json'), 'w+') as f:
        json.dump(conf, f, indent=2)

    return work_dir
