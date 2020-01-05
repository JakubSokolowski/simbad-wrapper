import os

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String

from database import Base


class Artifact(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    created_utc = Column(DateTime)
    size_kb = Column(Integer)
    name = Column(String())
    path = Column(String())
    file_type = Column(String())

    def get_workdir(self):
        return os.path.dirname(os.path.abspath(self.path)) if self.path is not None else None

    def __json__(self):
        return ['id', 'created_utc', 'size_kb', 'name', 'file_type']
