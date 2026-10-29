"""Admin-only runtime policy changes; immutable snapshots and durable audit first."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from configuration import get_manager, ConfigurationError
from .api import PREFIX, current, get_db, require_enabled
from . import service
from .errors import DomainError

router = APIRouter(prefix=PREFIX + '/configuration', tags=['configuration'], dependencies=[Depends(require_enabled)])

class RuntimePatch(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    expected_revision: int = Field(ge=1)
    changes: dict[str, int | float] = Field(min_length=1, max_length=2)

def admin(auth, db):
    if 'ADMIN' not in service.current_roles(db, auth.account): raise DomainError('forbidden')

@router.get('')
def snapshot(auth=Depends(current), db=Depends(get_db)):
    admin(auth, db)
    manager = get_manager()
    data = manager.public_snapshot()
    config = manager.snapshot.services.vehicle_catalog
    data['reloadable'] = {'services.vehicle_catalog.timeout_seconds': config.timeout_seconds,
                          'services.vehicle_catalog.retries': config.retries}
    return data

@router.patch('')
def update(data: RuntimePatch, auth=Depends(current), db=Depends(get_db)):
    admin(auth, db)
    def audit(event):
        service.record(db, auth.account, 'CONFIG_RUNTIME_CHANGED',
                       'revision:' + str(event['revision']) + ';' + ','.join(event['paths']))
        db.commit()
    try:
        return get_manager().reload(data.changes, expected_revision=data.expected_revision, audit=audit)
    except ConfigurationError as error:
        raise HTTPException(409, str(error)) from None
