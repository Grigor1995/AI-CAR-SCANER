"""Version 1 configuration contract; unknown fields and coercion are rejected."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

class App(Frozen):
    name: str = "AI Car Scanner"
    version: str = "0.6.0"
    language: Literal["en", "hy", "ru", "fr"] = "en"
    timezone: str = "UTC"
    platforms: tuple[str, ...] = ("desktop", "android", "ios")
    units: Literal["EU", "USA"] = "EU"

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try: ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError): raise ValueError('Unknown timezone') from None
        return value

class Native(Frozen):
    minimum_cpp: Literal[20] = 20
    preferred_cpp: Literal[23] = 23
    enabled: Literal[False] = False
    build_policy: Literal["toolchain_owned"] = "toolchain_owned"

class AI(Frozen):
    provider: Literal["llama-server", "openai-compatible", "placeholder"] = "llama-server"
    model_path: str = "models"
    endpoint: str = "http://127.0.0.1:8000"
    api_key_env: str = Field("OPENAI_API_KEY", pattern=r"^[A-Z_][A-Z0-9_]{0,127}$")
    context: int = Field(8192, ge=512, le=131072)
    temperature: float = Field(0.1, ge=0, le=2)
    max_tokens: int = Field(700, ge=64, le=32768)
    timeout_seconds: float = Field(300.0, ge=1, le=600)
    retries: int = Field(1, ge=0, le=3)
    offline: bool = True
    rag_enabled: bool = True
    rules_enabled: Literal[True] = True
    ml_enabled: Literal[False] = False

class Catalog(Frozen):
    mode: Literal["embedded", "remote"] = "embedded"
    service_id: Literal["vehicle-catalog"] = "vehicle-catalog"
    api_version: Literal["v1"] = "v1"
    url: str = "http://127.0.0.1:8011"
    token_env: Literal["AI_CAR_VEHICLE_SERVICE_TOKEN"] = "AI_CAR_VEHICLE_SERVICE_TOKEN"
    timeout_seconds: float = Field(2.0, ge=0.1, le=30)
    retries: int = Field(1, ge=0, le=2)
    enabled: bool = True
    health_path: Literal["/health"] = "/health"

class Services(Frozen):
    vehicle_catalog: Catalog = Field(default_factory=Catalog)
    backend_port: int = Field(8001, ge=1, le=65535)
    database_url_env: Literal["DATABASE_URL"] = "DATABASE_URL"

class OBD(Frozen):
    timeout_seconds: float = Field(3.0, ge=0.1, le=60)
    retries: int = Field(2, ge=0, le=5)
    poll_interval_ms: int = Field(500, ge=50, le=60000)
    autodetect: bool = True
    read_only: Literal[True] = True
    write_policy: Literal["explicit_authorized_operation"] = "explicit_authorized_operation"
    max_buffer_samples: int = Field(100000, ge=1000, le=1000000)

class Monitoring(Frozen):
    enabled: bool = True
    notifications_enabled: bool = True
    provider_credentials_env: str = Field("AI_CAR_NOTIFICATION_CREDENTIALS", pattern=r"^[A-Z_][A-Z0-9_]{0,127}$")
    delivery_mode: Literal["in_app_only"] = "in_app_only"

class UI(Frozen):
    theme: Literal["dark", "light"] = "dark"
    chart: Literal["analog", "linear"] = "analog"

class Updates(Frozen):
    enabled: Literal[False] = False
    signed_required: Literal[True] = True
    manifest_url: str = ""

class Marketplace(Frozen):
    enabled: bool = True
    purchase_enabled: Literal[False] = False
    checkout_enabled: Literal[False] = False
    payments_enabled: Literal[False] = False
    subscriptions_enabled: Literal[False] = False

class GlobalConfig(Frozen):
    schema_version: Literal[1] = 1
    app: App = Field(default_factory=App)
    native: Native = Field(default_factory=Native)
    ai: AI = Field(default_factory=AI)
    services: Services = Field(default_factory=Services)
    obd: OBD = Field(default_factory=OBD)
    monitoring: Monitoring = Field(default_factory=Monitoring)
    ui: UI = Field(default_factory=UI)
    updates: Updates = Field(default_factory=Updates)
    marketplace: Marketplace = Field(default_factory=Marketplace)
