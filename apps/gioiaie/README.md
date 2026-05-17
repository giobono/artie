# gioiaie

The gioiaie application implements **Phase 1 (typology development)** and **Phase 2 (saturation check)** of the Correlating Resonance methodology. It is one of four sibling applications under the ArtIE platform's flat `apps/` namespace; the others (`sanzognie`, `corres`, `pluralitie`) handle later phases.

This package is mounted by the platform at `/v1/gioiaie/`.

## Package layout

```
apps/gioiaie/
├── __init__.py         # Re-exports router for platform auto-discovery
├── router.py           # FastAPI router with endpoint definitions
├── prompts/
│   ├── reference/      # Open, citable prompts (filenames track methodology version)
│   └── production/     # Production-tuned variants (overlay at deploy time)
└── README.md           # This file
```

## Endpoints

| Path | Method | Status | Description |
|------|--------|--------|-------------|
| `/health` | GET | v0.9.3 | Liveness probe |
| `/phase1/consolidate` | POST | v0.9.3 (planned) | Phase 1 consolidation pass — server-side |

Additional Phase 1 and Phase 2 endpoints land in v0.10.0+ as the long-running task-ID polling pattern is established platform-side.

## Auto-discovery assumption

The platform's application discovery is assumed to:

1. Import `apps.gioiaie` (which re-exports `router` from `__init__.py`)
2. Mount that router at `/v1/gioiaie/`

If `GET /v1/gioiaie/health` returns 404 after a successful deploy, the most likely causes are, in order of likelihood:

1. **Deploy pipeline did not pick up the new directory.** Most likely cause on first commit. Check that `apps/gioiaie/` is present on the deployed filesystem.
2. **Auto-discovery convention is different.** The platform may expect a different attribute name (e.g. `app_router` rather than `router`), a different module location (e.g. `apps/gioiaie/main.py`), or an explicit registration step elsewhere. Confirm with the framework project before adjusting.
3. **Router defines its own prefix.** This module assumes the platform applies the `/v1/gioiaie/` prefix on mount. If the platform expects routers to define their own prefix, adjust `router.py` to `APIRouter(prefix="/v1/gioiaie", tags=["gioiaie"])`.

## Smoke test

Local (if running the API at `127.0.0.1:8000`):

```bash
curl -i http://127.0.0.1:8000/v1/gioiaie/health
```

Dev API:

```bash
curl -i https://api-dev.ebono.net/v1/gioiaie/health
```

Expected response in both cases:

```
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok","app":"gioiaie"}
```

This check should be run as the first step of every commit that adds a new `apps/<app_id>/` package, before any substantive endpoint work begins.
