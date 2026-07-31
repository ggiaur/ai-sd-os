"""Model selection: a 3-tier escalation ladder, not an upfront complexity guess.

Verified against Anthropic's official announcements (2026-07-31):
- Haiku 4.5  (claude-haiku-4-5-20251001) — $1 / $5 per million tokens (in/out)
- Sonnet 4.6 (claude-sonnet-4-6)         — $3 / $15 per million tokens
- Sonnet 5   (claude-sonnet-5)           — $2/$10 intro pricing through
                                            2026-08-31, then $3/$15

Sonnet 5 is Anthropic's most capable Sonnet-tier model but is not
categorically "the complex-task model" — pricing shifts over time (it is
currently CHEAPER than 4.6 during an introductory period) and capability
needs can't be reliably guessed from a task description upfront. The
defensible, professional pattern here is escalation-on-demonstrated-failure,
not guessing:

1. First attempt: light_model (Haiku) for simple WorkPackages, default_model
   (Sonnet 4.6) otherwise.
2. Middle retries: default_model — most failures are the kind an equally
   capable retry (with the failure feedback in the prompt) fixes.
3. Only the LAST retry before giving up escalates to escalation_model
   (Sonnet 5) — i.e. only once default_model has demonstrably failed
   repeatedly on this exact task, not because the task merely "looks" hard.

This applies identically to code generation (DeveloperAgent) and independent
review (TestRunner) — the same ladder, not two separately tuned ones.
"""

from contracts.work_package import WorkPackage

SIMPLE_TASK_COUNT_THRESHOLD = 1
SIMPLE_DESCRIPTION_LENGTH_THRESHOLD = 200


def is_simple_work_package(wp: WorkPackage) -> bool:
    total_description_length = sum(len(t.description) for t in wp.tasks)
    return (
        len(wp.tasks) <= SIMPLE_TASK_COUNT_THRESHOLD
        and total_description_length < SIMPLE_DESCRIPTION_LENGTH_THRESHOLD
    )


def select_model_for_attempt(
    wp: WorkPackage,
    retry_count: int,
    max_retries: int,
    light_model: str,
    default_model: str,
    escalation_model: str,
) -> str:
    """Pick a model for THIS attempt at this WorkPackage.

    retry_count: 0 on the first attempt, incrementing on each retry.
    max_retries: the pipeline's configured ceiling before PIPELINE_BLOCKED.
    """
    is_last_attempt = max_retries > 0 and retry_count >= max_retries - 1

    if is_last_attempt and retry_count > 0:
        # Only escalate once cheaper models have genuinely, repeatedly
        # failed on this specific task — not on a guess about difficulty.
        return escalation_model

    if retry_count == 0 and is_simple_work_package(wp):
        return light_model

    return default_model


# Backward-compatible convenience wrapper for simple (non-retry-aware) callers.
def select_model(wp: WorkPackage, light_model: str, strong_model: str) -> str:
    return light_model if is_simple_work_package(wp) else strong_model
