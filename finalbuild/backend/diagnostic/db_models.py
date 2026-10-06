from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from uuid import UUID
class Base(DeclarativeBase): pass
class VehicleRow(Base):
    __tablename__='vehicles'; id:Mapped[UUID]=mapped_column(primary_key=True); make:Mapped[str]=mapped_column(String(100)); model:Mapped[str]=mapped_column(String(100)); year:Mapped[int|None]=mapped_column(Integer); engine:Mapped[str|None]=mapped_column(String(100)); fuel:Mapped[list]=mapped_column(JSON,default=list); ecu:Mapped[str|None]=mapped_column(String(100)); metadata_json:Mapped[dict]=mapped_column('metadata',JSON,default=dict)
class DiagnosticSessionRow(Base):
    __tablename__='diagnostic_sessions'; id:Mapped[UUID]=mapped_column(primary_key=True); vehicle_id:Mapped[UUID|None]=mapped_column(ForeignKey('vehicles.id')); state:Mapped[str]=mapped_column(String(64)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow,onupdate=datetime.utcnow)
class EvidenceRow(Base):
    __tablename__='evidence'; id:Mapped[UUID]=mapped_column(primary_key=True); session_id:Mapped[UUID]=mapped_column(ForeignKey('diagnostic_sessions.id')); fact:Mapped[str]=mapped_column(Text); source:Mapped[str]=mapped_column(String(64)); status:Mapped[str]=mapped_column(String(32)); confidence:Mapped[float|None]=mapped_column(Float); source_ref:Mapped[str|None]=mapped_column(String(255)); metadata_json:Mapped[dict]=mapped_column('metadata',JSON,default=dict); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.utcnow)
