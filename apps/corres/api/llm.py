"""
CorRes LLM endpoint — v0.9.1.

Mounts /v1/corres/llm/messages and delegates to artie_platform.llm.client.
Hardcodes the beta tenancy and app identifiers per platform contract §4.3
and the v0.9.1 split brief.
"""

import uuid
from typing import Any, Union

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from artie_platform.llm.client import create_message
from artie_platform.llm.errors import SpendCeilingReached, UpstreamError

# v0.9.1 hardcoded values. tenant_id rolls over to artie_corres_v1 at the
# v1.0 release cut per platform contract §4.4. app_version should be sourced
# from package metadata; hardcoded here for clarity at the slice boundary.
APP_ID = "corres"
APP_VERSION = "0.9.1"
BETA_TENANT_ID = "artie_corres_v0"

router = APIRouter(prefix="/v1/corres/llm", tags=["corres-llm"])


class MessageRequest(BaseModel):
    system: str
    user: Union[str, list[dict[str, Any]]]
    max_tokens: int = Field(gt=0, le=8192)
    pinned_model: str | None = None
    task: str | None = None


class MessageResponse(BaseModel):
    text: str
    request_id: str


@router.post("/messages", response_model=MessageResponse)
async def messages(req: MessageRequest, request: Request) -> MessageResponse:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

    try:
        text = await create_message(
            system=req.system,
            user=req.user,
            max_tokens=req.max_tokens,
            app_id=APP_ID,
            app_version=APP_VERSION,
            tenant_id=BETA_TENANT_ID,
            model_pin=req.pinned_model,
            task=req.task,
            request_id=request_id,
        )
    except SpendCeilingReached:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "service_at_capacity",
                "message": "Service is temporarily at capacity. Please try again later.",
            },
        )
    except UpstreamError as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "upstream_error", "message": str(e)},
        )

    return MessageResponse(text=text, request_id=request_id)
