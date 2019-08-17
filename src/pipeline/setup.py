import json
import os

from env.constants import OUT_PATH

current_id = 0


def request_to_json(req):
    print(req)
    return json.loads(req.data.decode('utf8'))


def simulation_workdir_setup(conf, name) -> str:
    work_dir = OUT_PATH + '/SIM_{}_CONF_{}'.format(current_id, name)
    os.mkdir(work_dir)
    with open('{}/{}'.format(work_dir, name + '.json'), 'w+') as f:
        json.dump(conf, f, indent=2)

    return work_dir
