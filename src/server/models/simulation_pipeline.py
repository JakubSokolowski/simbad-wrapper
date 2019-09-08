from sqlalchemy import Column

from server import db


class SimulationPipeline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
