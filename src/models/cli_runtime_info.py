from sqlalchemy import Column, Integer, ForeignKey, Float

from database import Base


class CliRuntimeInfo(Base):
    __tablename__ = 'cli_runtime_infos'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    cpu = Column(Integer)
    memory = Column(Integer)
    progress = Column(Float)

    def __json__(self):
        return ['cpu', 'memory', 'progress']