import logging
from flask import Blueprint, send_file

artifact_api = Blueprint('artifact', __name__)
logger = logging.getLogger()


@artifact_api.route('/download/<path>', methods=['GET'])
def download(path: str):
    return send_file(path)
