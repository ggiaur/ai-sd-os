"""Best-effort startup check that the configured models actually exist.

Model availability changes over time — Anthropic deprecates and renames
models. Hardcoding a model ID and hoping it stays valid forever is exactly
the kind of silent assumption that breaks a pipeline months later with a
confusing API error deep inside a sprint run. This does one real API call
per configured model at startup (not per work package — that would be
wasteful) and reports clearly if something needs the human's attention,
rather than guessing at a replacement.
"""

import logging
from typing import Dict

logger = logging.getLogger("ModelValidator")

DOCS_URL = "https://platform.claude.com/docs/en/about-claude/models/overview"


def validate_models(api_key: str, models: Dict[str, str]) -> Dict[str, bool]:
    """Check each {label: model_id} against the real Anthropic API.

    Returns {label: is_available}. Never raises: a network hiccup or an API
    error here must not prevent the engine from starting — it should only
    inform, loudly, that a model may need to be reconfigured. Callers decide
    what to do with an unavailable model (e.g. fall back to a lower tier);
    this function only reports.
    """
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.warning(f"Could not initialize Anthropic client for model validation: {e}")
        # Don't block startup over a validation-infrastructure problem —
        # assume configured models are fine and let real usage surface issues.
        return {label: True for label in models}

    results: Dict[str, bool] = {}
    for label, model_id in models.items():
        try:
            client.models.retrieve(model_id)
            results[label] = True
        except Exception as e:
            logger.warning(
                f"Configured {label} model '{model_id}' failed validation ({e}) — "
                f"it may be deprecated or renamed. Check {DOCS_URL} and update "
                f"KernelConfig / your .env accordingly."
            )
            results[label] = False
    return results
