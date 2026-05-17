"""
gioianie router — defines endpoints under /v1/gioianie/.

The router is mounted by the ArtIE platform at /v1/gioianie/; paths in this
module are defined relative to that prefix. The platform's application
discovery imports this package and reads the `router` attribute exported
from __init__.py.

v0.9.3 endpoints:
    GET /health — liveness probe (this file)

v0.9.3 endpoints landing in subsequent commits on the feature branch:
    POST /phase1/consolidate — server-side Phase 1 consolidation pass

Subsequent versions (v0.10.0+) will add the remaining Phase 1 and Phase 2
workflows. Each endpoint lives as its own route handler in this module
until the file grows large enough to justify splitting by phase.
"""

from fastapi import APIRouter

router = APIRouter(tags=["gioianie"])


@router.get("/health")
async def health() -> dict:
    """
    Liveness probe for the gioianie application.

    Returns 200 with a minimal payload if the package has loaded and the
    router is mounted. A 404 from this endpoint after deployment indicates
    the package did not load — see README.md for diagnostic notes.

    This endpoint is intentionally trivial: it has no dependencies on
    prompts, models, or upstream services. Its sole purpose is to make
    deploy-pipeline failures visible at five-second cost rather than buried
    inside a substantive endpoint failure.
    """
    return {"status": "ok", "app": "gioianie"}
