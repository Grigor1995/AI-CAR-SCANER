"""Catalog port: same domain functions embedded or behind a bounded HTTP adapter."""
import json
import os
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from fastapi import HTTPException
from configuration import get_manager
from .correlation import correlation_id

OPERATIONS = {"stats", "makes", "models", "fitments", "profile"}
MAX_RESPONSE = 4 * 1024 * 1024

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def credential(environ=None):
    env = os.environ if environ is None else environ
    token = env.get("AI_CAR_VEHICLE_SERVICE_TOKEN", "")
    if len(token) < 32 or len(token) > 512 or not token.isascii() or any(c.isspace() for c in token):
        raise HTTPException(503, "Catalog service credential is not configured")
    return token

def embedded(operation, parameters):
    from vehicle import catalog_registry
    functions = {"stats": catalog_registry.registry_stats, "makes": catalog_registry.makes,
                 "models": catalog_registry.models, "fitments": catalog_registry.fitments,
                 "profile": catalog_registry.vehicle_protocol_profile}
    return functions[operation](**parameters)

def catalog(operation, **parameters):
    if operation not in OPERATIONS: raise ValueError("Unknown catalog operation")
    config = get_manager().snapshot.services.vehicle_catalog
    if not config.enabled: raise HTTPException(503, "Catalog service disabled")
    if config.mode == "embedded": return embedded(operation, parameters)
    # Only idempotent reads are retried. Redirects never forward the bearer token.
    query = urlencode({key: value for key, value in parameters.items() if value is not None})
    request = Request(config.url.rstrip("/") + "/internal/v1/catalog/" + operation + "?" + query,
                      headers={"Authorization": "Bearer " + credential(),
                               "X-Correlation-ID": correlation_id.get() or secrets.token_hex(16)})
    for attempt in range(config.retries + 1):
        try:
            with build_opener(NoRedirect()).open(request, timeout=config.timeout_seconds) as response:
                payload = response.read(MAX_RESPONSE + 1)
                if len(payload) > MAX_RESPONSE: raise ValueError("oversized response")
                result = json.loads(payload)
                expected = list if operation in {"makes", "models", "fitments"} else dict
                if not isinstance(result, expected): raise ValueError("invalid response contract")
                if operation == 'makes' and not all(isinstance(item, str) for item in result):
                    raise ValueError('invalid make DTO')
                if operation in {'models', 'fitments'} and not all(isinstance(item, dict) and isinstance(item.get('make'), str) and isinstance(item.get('model'), str) for item in result):
                    raise ValueError('invalid vehicle DTO')
                if operation == 'stats' and not isinstance(result.get('make_count'), int):
                    raise ValueError('invalid stats DTO')
                if operation == 'profile' and result.get('status') not in {'seeded_not_vin_verified', 'not_in_seed_catalog'}:
                    raise ValueError('invalid profile DTO')
                return result
        except HTTPError as error:
            error.close()
            if error.code not in {429, 502, 503, 504} or attempt == config.retries: break
        except (URLError, TimeoutError, OSError):
            if attempt == config.retries: break
        except (ValueError, UnicodeError): break
    raise HTTPException(503, "Vehicle catalog temporarily unavailable")
