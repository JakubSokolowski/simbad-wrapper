import enum
import os
from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Step(enum.Enum):
    CONF = 0
    CLI = 1
    ANALYZER = 2
    REPORT = 3
    FINISHED = 4


class SimulationModel(Base):
    __tablename__ = 'simulations'

    id = Column(Integer, primary_key=True)
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    current_step = Column(Enum(Step))
    current_step_celery_id = Column(String())
    workdir = Column(String())
    name = Column(String(50), unique=False)
    steps = relationship("SimulationStepModel", backref="simulations")
    artifacts = relationship("ArtifactModel", backref="simulations")


class SimulationStepModel(Base):
    __tablename__ = 'steps'
    RELATIONSHIPS_TO_DICT = True

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    origin = Column(Enum(Step))
    celery_id = Column(String())
    cli_runtime_info = relationship("CliRuntimeInfoModel", uselist=False, backref="steps")
    artifacts = relationship("ArtifactModel", backref="steps")

    def __json__(self):
        return ['id', 'simulation_id', 'started_utc', 'finished_utc', 'origin', 'artifacts', 'cli_runtime_info']


class ArtifactModel(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    created_utc = Column(DateTime)
    size_kb = Column(Integer)
    path = Column(String())

    def __json__(self):
        return ['id', 'created_utc', 'size_kb', 'path']

    def get_workdir(self):
        return os.path.dirname(os.path.abspath(self.path)) if self.path is not None else None


@dataclass
class Artifact:
    id: int
    step_id: int
    simulation_id: int
    created_utc: DateTime
    size_kb: int
    path: str

    def __init__(self, **kwargs):
        print('Artifact concrete init', kwargs.items())
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __json__(self):
        return ['id', 'created_utc', 'size_kb', 'path']

    def get_workdir(self):
        return os.path.dirname(os.path.abspath(self.path)) if self.path is not None else None


class CliRuntimeInfoModel(Base):
    __tablename__ = 'cli_runtime_infos'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    cpu = Column(Integer)
    memory = Column(Integer)

    def __json__(self):
        return ['cpu', 'memory']
