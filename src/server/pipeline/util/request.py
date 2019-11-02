import json


def request_to_json(req) -> dict:
    return json.loads(req.data.decode('utf8'))
