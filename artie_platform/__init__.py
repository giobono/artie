"""
ArtIE platform — shared services consumed by applications.

Contains LLM abstraction, storage, file services, export, observability,
auth, and tenancy primitives. Application code may import only from
artie_platform.* or from within its own apps/<app_id>/ namespace.

The directory is named artie_platform/ rather than platform/ to avoid
shadowing the Python standard library's `platform` module, which is
imported by httpx, uvicorn, and other dependencies.
"""
