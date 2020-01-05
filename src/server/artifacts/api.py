import logging

from flask import Blueprint, send_file, jsonify, make_response

from database import db_session
from models.artifact import Artifact

artifact_api = Blueprint('artifact', __name__)
logger = logging.getLogger()


@artifact_api.route('/<artifact_id>', methods=['GET'])
def get_info(artifact_id: int):
    artifact: Artifact = db_session.query(Artifact).get(artifact_id)
    if artifact is not None:
        return jsonify(artifact)
    return 404


@artifact_api.route('/<artifact_id>/download', methods=['GET'])
def download(artifact_id: int):
    artifact: Artifact = db_session.query(Artifact).get(artifact_id)
    print('Downloading...', artifact)
    response = make_response(send_file(artifact.path, as_attachment=True))
    response.headers["Content-Type"] = "application/pdf; charset=utf-8"
    return response
