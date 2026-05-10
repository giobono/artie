"""
Model registry — v0.9.1 stub.

Applications may select models by task semantics (open_coding,
structured_extraction, interpretation) or by identifier pinning. For
v0.9.1 the registry mapping is unpopulated: every task resolves to
PINNED_DEFAULT, and identifier pinning is the exclusive selector.

The registry mapping will be populated in v0.9.2 once application-side
evals exist to validate task-to-model assignments.
"""

PINNED_DEFAULT = "claude-sonnet-4-20250514"

TASK_TAXONOMY = {
    "open_coding",
    "structured_extraction",
    "interpretation",
}


def resolve_model(task: str | None, model_pin: str | None) -> tuple[str, bool]:
    """
    Return (model_identifier, was_pinned).

    model_pin wins if provided. was_pinned is exposed so observability
    can record whether a call used identifier pinning or task-based
    resolution (per platform contract §6).

    Tasks not in TASK_TAXONOMY are accepted silently and resolve to
    PINNED_DEFAULT — applications using a task name we don't yet recognise
    are not blocked.
    """
    if model_pin:
        return model_pin, True
    return PINNED_DEFAULT, False
