"""Durable business aggregates, reusing Account/Ownership and DiagnosticSession JSON."""
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .models import Base, uid, utcnow
from datetime import datetime


class Settings(Base):
    __tablename__ = 'ecosystem_settings'
    account_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class DiagnosticRecord(Base):
    __tablename__ = 'ecosystem_diagnostics'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey('vehicle_profiles.id'), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'))
    center_id: Mapped[str | None] = mapped_column(ForeignKey('ecosystem_service_centers.id'), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {'version_id_col': version}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StaffInvitation(Base):
    __tablename__ = 'ecosystem_staff_invitations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    center_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_service_centers.id'))
    account_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'), index=True)
    role: Mapped[str] = mapped_column(String(16))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)


class WorkOrder(Base):
    __tablename__ = 'ecosystem_work_orders'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    center_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_service_centers.id'), index=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey('vehicle_profiles.id'))
    title: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str] = mapped_column(String(10000), default='')
    status: Mapped[str] = mapped_column(String(20), default='OPEN')
    __table_args__ = (CheckConstraint("status IN ('OPEN','IN_PROGRESS','COMPLETED')", name='ck_eco_order_status'),)


class Merchant(Base):
    __tablename__ = 'ecosystem_merchants'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = 'ecosystem_products'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_merchants.id'), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    price_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    stock: Mapped[int] = mapped_column(Integer)
    listed: Mapped[bool] = mapped_column(Boolean, default=False)
    moderation: Mapped[str] = mapped_column(String(16), default='PENDING')
    __table_args__ = (CheckConstraint('price_minor >= 0 AND stock >= 0', name='ck_eco_product_values'),
                      CheckConstraint("moderation IN ('PENDING','APPROVED','REJECTED')", name='ck_eco_moderation'))


class Offer(Base):
    __tablename__ = 'ecosystem_offers'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    product_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_products.id'), index=True)
    basis_points: Mapped[int] = mapped_column(Integer)
    audience: Mapped[str] = mapped_column(String(16))
    center_id: Mapped[str | None] = mapped_column(ForeignKey('ecosystem_service_centers.id'), nullable=True)
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1)
    coupon: Mapped[str | None] = mapped_column(String(40), nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (CheckConstraint('basis_points BETWEEN 1 AND 9000 AND minimum_quantity > 0', name='ck_eco_offer_values'),)


class MonitoringSchedule(Base):
    __tablename__ = 'ecosystem_monitoring_schedules'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'), index=True)
    profile_id: Mapped[str] = mapped_column(ForeignKey('vehicle_profiles.id'))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[dict] = mapped_column(JSON)
    next_due: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    __table_args__ = (UniqueConstraint('owner_id','profile_id',name='uq_eco_monitoring_vehicle'),)


class MonitoringRun(Base):
    __tablename__ = 'ecosystem_monitoring_runs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    schedule_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_monitoring_schedules.id'), index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    reason: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint('schedule_id','due_at',name='uq_eco_monitoring_run'),
                      CheckConstraint("status IN ('DEFERRED','MISSED','FAILED','COMPLETED')",name='ck_eco_monitoring_status'))


class Notification(Base):
    __tablename__ = 'ecosystem_notifications'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    account_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_accounts.id'), index=True)
    kind: Mapped[str] = mapped_column(String(60))
    payload: Mapped[dict] = mapped_column(JSON)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DirectoryDetails(Base):
    __tablename__ = 'ecosystem_directory_details'
    center_id: Mapped[str] = mapped_column(ForeignKey('ecosystem_service_centers.id'), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)


class TechnicalReference(Base):
    __tablename__ = 'ecosystem_technical_references'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    kind: Mapped[str] = mapped_column(String(16))
    payload: Mapped[dict] = mapped_column(JSON)
