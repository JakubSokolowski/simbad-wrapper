import logging

from flask import Blueprint, send_file, jsonify

from database import db_session
from models.simulation import Artifact
from server.artifacts.utils import compress_artifact

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
    archive_path = compress_artifact(artifact.path)
    return send_file(archive_path)
