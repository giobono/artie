"""
Platform LLM abstraction — v0.9.1.

Single point of integration for outbound calls to language model providers.
Tags every call with tenant_id, app_id, app_version, request_id per platform
contract §7. Returns provider response content as a single text string;
structured-output parsing (repairJSON) remains application-side in v0.9.1
and migrates to the platform in v0.9.2.
"""

import logging
import os
import uuid
from typing import Any, Union

import httpx

from .errors import SpendCeilingReached, UpstreamError
from .registry import resolve_model

logger = logging.getLogger("artie_platform.llm")

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


def _llm_disabled() -> bool:
    """
    Kill-switch for the LLM service.

    Set ARTIE_LLM_DISABLED=1 to take the endpoint offline; calls return
    SpendCeilingReached, which the application layer translates to HTTP 503.
    The metered rolling-spend ceiling (platform contract §6.1) is deferred
    to v0.9.2; this kill-switch is the v0.9.1 cost-bounding mechanism.
    """
    return os.getenv("ARTIE_LLM_DISABLED", "0") == "1"


async def create_message(
    *,
    system: str,
    user: Union[str, list[dict[str, Any]]],
    max_tokens: int,
    app_id: str,
    app_version: str,
    tenant_id: str,
    model_pin: str | None = None,
    task: str | None = None,
    request_id: str | None = None,
) -> str:
    """
    Issue an LLM call through the platform abstraction.

    Returns the concatenated text content of the response. Raises
    UpstreamError on provider failure, SpendCeilingReached when the
    kill-switch is set.
    """
    request_id = request_id or str(uuid.uuid4())

    if _llm_disabled():
        logger.warning(
            "llm_call_blocked_by_kill_switch",
            extra={"tenant_id": tenant_id, "app_id": app_id, "request_id": request_id},
        )
        raise SpendCeilingReached("LLM service at capacity")

    api_key = os.environ["ANTHROPIC_API_KEY"]
    model, was_pinned = resolve_model(task=task, model_pin=model_pin)

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }

    log_tags = {
        "tenant_id": tenant_id,
        "app_id": app_id,
        "app_version": app_version,
        "request_id": request_id,
        "model": model,
        "model_pinned": was_pinned,
    }
    logger.info("llm_call_attempt", extra={**log_tags, "max_tokens": max_tokens})

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=body)
        except httpx.HTTPError as e:
            logger.warning("llm_call_transport_error", extra={**log_tags, "error": str(e)})
            raise UpstreamError(f"Transport error: {e}") from e

    if resp.status_code != 200:
        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text)
        except Exception:
            err_msg = resp.text
        logger.warning(
            "llm_call_upstream_error",
            extra={**log_tags, "status": resp.status_code, "error": err_msg},
        )
        raise UpstreamError(f"Provider {resp.status_code}: {err_msg}")

    data = resp.json()
    usage = data.get("usage", {})

    # Per platform contract §7: token counts recorded per call from day one
    # so historical cost data is reconstructible by tenant and application
    # when billing arrives.
    logger.info(
        "llm_call_complete",
        extra={
            **log_tags,
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        },
    )

    return "".join(b.get("text", "") for b in data.get("content", []))
