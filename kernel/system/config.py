import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

@dataclass
class KernelConfig:
    max_retries: int = 3
    storage_dir_name: str = ".ai-sd-os"
    auto_checkpoint: bool = True
    mock_mode: bool = False
    # 3-tier model escalation ladder (see sdk/model_selector.py). Model IDs
    # and pricing verified against Anthropic's official announcements as of
    # 2026-07-31 — re-verify before changing, these strings are load-bearing:
    #   Haiku 4.5  claude-haiku-4-5-20251001  $1 / $5 per Mtok (in/out)
    #   Sonnet 4.6 claude-sonnet-4-6          $3 / $15 per Mtok
    #   Sonnet 5   claude-sonnet-5            $2/$10 intro (until 2026-08-31), then $3/$15
    #
    # Cheapest/fastest — first attempt on simple WorkPackages, and review.
    light_model: str = "claude-haiku-4-5-20251001"
    # Default — first attempt on non-simple WorkPackages, and all mid-retries.
    ai_model: str = "claude-sonnet-4-6"
    # Escalation-only — used solely on the LAST retry before giving up, i.e.
    # only once ai_model has demonstrably, repeatedly failed on this task.
    escalation_model: str = "claude-sonnet-5"
    api_key: Optional[str] = None
    default_timeout_minutes: int = 30
    require_human_gates: bool = True
    # Which AIProvider backs codegen/review when not in mock_mode:
    # "anthropic" (default, one-shot API call) or "claude_code_cli"
    # (file-aware, iterative — shells out to the `claude` CLI).
    provider: str = "anthropic"
    # Validate light_model/ai_model/escalation_model against the real
    # Anthropic API at startup (one call per model) and warn loudly if any
    # is deprecated/renamed, instead of finding out mid-pipeline. Costs a
    # few API calls at startup; disable if that's undesirable.
    validate_models_at_startup: bool = True

    @classmethod
    def from_env(cls, cwd: Optional[Path] = None, mock: bool = False) -> "KernelConfig":
        from dotenv import load_dotenv
        if cwd:
            env_path = cwd / ".env"
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
        load_dotenv()

        return cls(
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            mock_mode=mock or (os.getenv("MOCK_MODE", "false").lower() == "true"),
            light_model=os.getenv("LIGHT_MODEL", "claude-haiku-4-5-20251001"),
            ai_model=os.getenv("AI_MODEL", "claude-sonnet-4-6"),
            escalation_model=os.getenv("ESCALATION_MODEL", "claude-sonnet-5"),
            api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
            provider=os.getenv("AI_SD_OS_PROVIDER", "anthropic"),
            validate_models_at_startup=os.getenv("VALIDATE_MODELS_AT_STARTUP", "true").lower() == "true",
        )
