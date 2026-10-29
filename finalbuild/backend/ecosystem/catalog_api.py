"""Existing account boundary remains authoritative for the v2 catalog gateway."""
from copy import deepcopy
from fastapi import APIRouter, Depends
from api import vehicle_registry_routes as legacy
from .api import current, require_enabled, PREFIX
router = APIRouter(prefix=PREFIX + "/catalog", tags=["vehicle-catalog"],
                   dependencies=[Depends(require_enabled), Depends(current)])
for path, endpoint in (("stats", legacy.stats), ("makes", legacy.global_makes),
                       ("models", legacy.global_models), ("fitments", legacy.global_fitments),
                       ("portrait", legacy.local_portrait)):
    router.add_api_route("/" + path, endpoint, methods=["GET"])


@router.get('/profile')
def profile(value: dict = Depends(legacy.vehicle_profile)):
    # Internal read-model links retain legacy semantics. At the authenticated
    # gateway, image links must stay inside the same account boundary.
    result = deepcopy(value)
    for name, url in result.get('image', {}).items():
        if isinstance(url, str) and url.startswith('/api/v1/vehicle-registry/'):
            result['image'][name] = url.replace('/api/v1/vehicle-registry/', PREFIX + '/catalog/', 1)
    return result


@router.get('/photo')
def photo(value: dict = Depends(legacy.photo)):
    result = dict(value)
    result['fallback_generated_portrait'] = result['fallback_generated_portrait'].replace(
        '/api/v1/vehicle-registry/', PREFIX + '/catalog/', 1)
    return result
