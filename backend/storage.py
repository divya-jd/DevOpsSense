import os
from datetime import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./devopssense.db")
engine = create_engine(DB_URL, echo=False, future=True)

class Base(DeclarativeBase): pass

class PipelineEvent(Base):
    __tablename__ = "pipeline_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(16))           # github | jenkins
    pipeline: Mapped[str] = mapped_column(String(256))        # workflow/job name
    run_id: Mapped[str] = mapped_column(String(128))
    repo_or_project: Mapped[str] = mapped_column(String(256))
    branch: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(32))           # success, failure...
    duration_ms: Mapped[int] = mapped_column(BigInteger)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)

def init_db():
    Base.metadata.create_all(engine)

def insert_event(**kwargs):
    with Session(engine) as s:
        ev = PipelineEvent(**kwargs)
        s.add(ev)
        s.commit()
        return ev.id
