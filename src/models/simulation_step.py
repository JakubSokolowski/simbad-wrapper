from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship

from database import Base


class SimulationStep(Base):
    __tablename__ = 'steps'
    RELATIONSHIPS_TO_DICT = True

    id = Column(Integer, primary_key=True)
    simulation_id = Column(Integer, ForeignKey('simulations.id'))
    started_utc = Column(DateTime)
    finished_utc = Column(DateTime)
    origin = Column(String())
    status = Column(String())
    error_message = Column(String())
    celery_id = Column(String())
    cli_runtime_info = relationship("CliRuntimeInfo", uselist=False, backref="steps")
    analyzer_runtime_info = relationship("AnalyzerRuntimeInfo", uselist=False, backref="steps")
    artifacts = relationship("Artifact", backref="steps")

    def __json__(self):
        return ['id', 'simulation_id', 'started_utc', 'finished_utc', 'origin', 'status', 'artifacts', 'cli_runtime_info',
                'analyzer_runtime_info']