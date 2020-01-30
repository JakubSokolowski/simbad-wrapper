from sqlalchemy import Column, Integer, ForeignKey, Boolean, Float, String

from database import Base


class AnalyzerRuntimeInfo(Base):
    __tablename__ = 'analyzer_runtime_infos'

    id = Column(Integer, primary_key=True)
    step_id = Column(Integer, ForeignKey('steps.id'))
    is_finished = Column(Boolean)
    progress = Column(Float)
    error = Column(String)

    def __json__(self):
        return ['progress', 'error']
