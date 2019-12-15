import enum
import os

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from database import Base


class Step(enum.Enum):
    CONF = 0
    CLI = 1
    ANALYZER = 2
    REPORT = 3
    FINISHED = 4


class Simulation(Base):
    __tablename__ = 'simulations'

    id = Column(Integer, primary_key=True)
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    current_step = Column(String())
    current_step_id = Column(Integer)
    workdir = Column(String())
    name = Column(String(50), unique=False)
    steps = relationship("SimulationStep", backref="simulations")
    artifacts = relationship("Artifact", backref="simulations")

    def __json__(self):
        return ['id', 'started_utc', 'finished_utc', 'current_step', 'current_step_id', 'steps']


class SimulationStep(Base):
    __tablename__ = 'steps'
    RELATIONSHIPS_TO_DICT = True

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    origin = Column(String())
    celery_id = Column(String())
    cli_runtime_info = relationship("CliRuntimeInfo", uselist=False, backref="steps")
    analyzer_runtime_info = relationship("AnalyzerRuntimeInfo", uselist=False, backref="steps")
    artifacts = relationship("Artifact", backref="steps")

    def __json__(self):
        return ['id', 'simulation_id', 'started_utc', 'finished_utc', 'origin', 'artifacts', 'cli_runtime_info',
                'analyzer_runtime_info']


class Artifact(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    created_utc = Column(DateTime)
    size_kb = Column(Integer)
    path = Column(String())

    def get_workdir(self):
        return os.path.dirname(os.path.abspath(self.path)) if self.path is not None else None

    def __json__(self):
        return ['id', 'created_utc', 'size_kb', 'path']


class CliRuntimeInfo(Base):
    __tablename__ = 'cli_runtime_infos'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    cpu = Column(Integer)
    memory = Column(Integer)

    def __json__(self):
        return ['cpu', 'memory']


class AnalyzerRuntimeInfo(Base):
    __tablename__ = 'analyzer_runtime_infos'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    is_finished = Column(Boolean)
    progress = Column(Float)

    def __json__(self):
        return ['progress']
