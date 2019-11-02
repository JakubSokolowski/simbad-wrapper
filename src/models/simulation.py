import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
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
    current_step = Column(Enum(Step))
    current_step_celery_id = Column(String())
    workdir = Column(String())
    name = Column(String(50), unique=False)
    steps = relationship("SimulationStep", backref="simulations")
    artifacts = relationship("Artifact", backref="simulations")


class SimulationStep(Base):
    __tablename__ = 'steps'

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    origin = Column(Enum(Step))
    celery_id = Column(String())
    artifacts = relationship("Artifact", backref="steps")
    simulation = relationship("Simulation", back_populates="steps")


class Artifact(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    step_id = Column(Integer, ForeignKey('steps.id'))
    created_utc = Column(DateTime)
    size_kb = Column(Integer)
    path = Column(String())
    simulation = relationship("Simulation", back_populates="artifacts")
    step = relationship("SimulationStep", back_populates="artifacts")

