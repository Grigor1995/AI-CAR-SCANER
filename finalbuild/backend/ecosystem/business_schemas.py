"""Strict boundary contracts; monetary amounts are integer minor currency units."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import Field, HttpUrl, field_validator, model_validator
from .schemas import Input, ProfileFields


class SettingsInput(Input):
    language: Literal['en','hy','ru','fr'] = 'en'
    units: Literal['EU','USA'] = 'EU'
    pressure: Literal['kPa','bar','psi'] = 'kPa'
    consumption: Literal['L/100km','km/L','mpg_US'] = 'L/100km'
    theme: Literal['dark','light'] = 'dark'
    timezone: str = 'UTC'
    email_alerts: bool = False
    sms_alerts: bool = False
    push_alerts: bool = False
    severity: Literal['LOW','MEDIUM','HIGH'] = 'HIGH'
    quiet_start_hour: int = Field(default=22,ge=0,le=23)
    quiet_end_hour: int = Field(default=8,ge=0,le=23)
    alert_interval_minutes: int = Field(default=1440,ge=15,le=10080)
    _timezone_valid = field_validator('timezone')(ProfileFields.timezone_exists.__func__)


class NewDiagnostic(Input):
    profile_id: UUID
    center_id: UUID | None = None


class EvidenceInput(Input):
    symptom: str = Field(default='',max_length=5000)
    dtcs: list[str] = Field(default_factory=list,max_length=100)
    @field_validator('dtcs')
    @classmethod
    def valid_codes(cls,codes):
        import re
        if any(not re.fullmatch(r'[PBCU][0-3][0-9A-F]{3}',c) for c in codes):raise ValueError('Invalid DTC')
        return list(dict.fromkeys(codes))


class TestInput(Input):
    result: Literal['PASS','FAIL','UNKNOWN','INCOMPLETE']
    measurements: dict[str,float] = Field(default_factory=dict,max_length=100)
    notes: str = Field(default='',max_length=3000)
    @field_validator('measurements')
    @classmethod
    def finite(cls,values):
        import math
        if any(not math.isfinite(v) for v in values.values()):raise ValueError('Finite measurements required')
        return values


class BridgeInput(Input):
    timestamp_ms: int = Field(ge=0)
    responses: dict[str,str] = Field(max_length=32)
    @field_validator('responses')
    @classmethod
    def limited(cls,values):
        if any(len(k)>16 or len(v)>32000 for k,v in values.items()):raise ValueError('Response too large')
        return values


class StaffInviteInput(Input):
    account_id: UUID
    role: Literal['admin','technician','viewer']


class OrderInput(Input):
    profile_id: UUID
    title: str = Field(min_length=1,max_length=300)


class OrderPatch(Input):
    status: Literal['OPEN','IN_PROGRESS','COMPLETED']
    notes: str = Field(default='',max_length=10000)


class MerchantInput(Input):
    name: str = Field(min_length=1,max_length=200)
    address: str = Field(min_length=1,max_length=500)
    phone: str | None = None
    _phone_valid = field_validator('phone')(ProfileFields.international_mobile.__func__)


class Fitment(Input):
    make: str = Field(min_length=1,max_length=100)
    model: str = Field(min_length=1,max_length=100)
    engine: str = Field(min_length=1,max_length=100)
    year_from: int = Field(ge=1886,le=2100)
    year_to: int = Field(ge=1886,le=2100)
    @model_validator(mode='after')
    def ordered(self):
        if self.year_from>self.year_to:raise ValueError('Invalid production interval')
        return self


class ProductInput(Input):
    name: str = Field(min_length=1,max_length=200)
    category: Literal['PART','ACCESSORY','DIAGNOSTIC_DEVICE','EQUIPMENT','MAINTENANCE']
    part_number: str = Field(default='',max_length=100)
    description: str = Field(default='',max_length=4000)
    price_minor: int = Field(ge=0,le=10**12,strict=True)
    currency: Literal['AMD','USD','EUR','RUB']
    stock: int = Field(ge=0,le=10**8,strict=True)
    listed: bool = False
    image_url: HttpUrl | None = None
    compatibility: list[Fitment] = Field(default_factory=list,max_length=100)
    @field_validator('image_url')
    @classmethod
    def https(cls,value):
        if value is not None and value.scheme!='https':raise ValueError('HTTPS required')
        return value


class OfferInput(Input):
    basis_points: int = Field(ge=1,le=9000)
    audience: Literal['PUBLIC','CUSTOMER','CENTER'] = 'PUBLIC'
    center_id: UUID | None = None
    minimum_quantity: int = Field(default=1,ge=1,le=100000)
    coupon: str | None = Field(default=None,pattern=r'^[A-Z0-9_-]{3,40}$')
    starts_at: datetime
    ends_at: datetime
    @model_validator(mode='after')
    def valid(self):
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None or self.ends_at<=self.starts_at:raise ValueError('Ordered timezone-aware dates required')
        if (self.audience=='CENTER')!=(self.center_id is not None):raise ValueError('CENTER offers require center_id only')
        return self


class QuoteInput(Input):
    quantity: int = Field(default=1,ge=1,le=100000)
    center_id: UUID | None = None
    coupon: str | None = Field(default=None,max_length=40)
    profile_id: UUID | None = None


class ScheduleInput(Input):
    profile_id: UUID
    enabled: bool = True
    consent: Literal[True]
    cadence: Literal['DAILY','WEEKLY','CUSTOM'] = 'DAILY'
    timezone: str = 'UTC'
    hour: int = Field(default=9,ge=0,le=23)
    custom_interval_minutes: int = Field(default=1440,ge=60,le=10080)
    _timezone_valid = field_validator('timezone')(ProfileFields.timezone_exists.__func__)


class DirectoryInput(Input):
    city: str = Field(min_length=1,max_length=100)
    services: list[str] = Field(default_factory=list,max_length=50)
    makes: list[str] = Field(default_factory=list,max_length=50)
    engines: list[str] = Field(default_factory=list,max_length=50)
    working_hours: str = Field(default='',max_length=500)
    email: str = Field(default='',max_length=254)


class ReferenceInput(Input):
    kind: Literal['REPAIR','WIRING']
    title: str = Field(min_length=1,max_length=300)
    fitment: Fitment
    source_url: HttpUrl
    license: str = Field(min_length=1,max_length=500)
    instructions: str = Field(min_length=1,max_length=20000)
    safety_warnings: list[str] = Field(min_length=1,max_length=30)
    tools: list[str] = Field(default_factory=list,max_length=100)
    professional_required: bool = True
    _https = field_validator('source_url')(ProductInput.https.__func__)


class AdminAccountPatch(Input):
    active: bool
    roles: list[Literal['USER','CUSTOMER','ADMIN','MARKET']] = Field(min_length=1,max_length=4)


class Approval(Input):
    active: bool = True
    verified: bool = True


class Moderation(Input):
    status: Literal['APPROVED','REJECTED']


# Output models keep SQL internals/password hashes out of OpenAPI and responses.
from pydantic import BaseModel
from diagnostic.models import DiagnosticSession


class DiagnosticOutput(BaseModel):
    id: UUID
    session: DiagnosticSession
    version: int | None = None


class ProductOutput(ProductInput):
    id: UUID
    merchant_id: UUID
    moderation: Literal['PENDING','APPROVED','REJECTED']
    compatibility_status: Literal['SELLER_CLAIM_UNVERIFIED']


class QuoteOutput(BaseModel):
    product_id: UUID
    quantity: int
    currency: str
    subtotal_minor: int
    discount_minor: int
    total_minor: int
    offer_id: UUID | None
    compatibility: Literal['UNKNOWN','SELLER_CLAIM_UNVERIFIED','NO_MATCHING_CLAIM']
    checkout_available: Literal[False]
    stock_reserved: Literal[False]


class WorkOrderOutput(BaseModel):
    id: UUID
    title: str
    notes: str
    status: Literal['OPEN','IN_PROGRESS','COMPLETED']
    center_id: UUID | None = None


class ScheduleOutput(BaseModel):
    id: UUID
    next_due: datetime
    enabled: bool
    payload: ScheduleInput
    profile_id: UUID | None = None


class RunOutput(BaseModel):
    id: UUID
    status: Literal['DEFERRED','MISSED','FAILED','COMPLETED']
    reason: str
    due_at: datetime


class NavigationPage(BaseModel):
    key: str
    label: str
    path: str


class NavigationOutput(BaseModel):
    workspace: Literal['USER','CUSTOMER','ADMIN','MARKET']
    primary: bool
    pages: list[NavigationPage]
