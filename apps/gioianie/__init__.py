"""
gioiaie — Phase 1 (typology development) and Phase 2 (saturation check)
application of the Correlating Resonance methodology.

This package exposes a FastAPI router that the ArtIE platform mounts at
/v1/gioiaie/ during application discovery (per platform contract §4).
Endpoints are defined in router.py with paths relative to that prefix.
"""

from .router import router

__all__ = ["router"]
