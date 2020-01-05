import enum

from sqlalchemy import Column, Integer, String, DateTime
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


