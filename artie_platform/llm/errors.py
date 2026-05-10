"""Typed exceptions for the LLM abstraction."""


class LLMError(Exception):
    """Base for platform LLM errors."""


class UpstreamError(LLMError):
    """Provider returned an error or was unreachable."""


class SpendCeilingReached(LLMError):
    """
    Spend ceiling reached; service returns 'at capacity' to the caller.

    In v0.9.1 this is raised only when the kill-switch env var
    ARTIE_LLM_DISABLED is set. The metered rolling-spend ceiling described
    in platform contract §6.1 is deferred to v0.9.2.
    """
