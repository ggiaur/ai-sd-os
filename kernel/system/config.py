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
    ai_model: str = "claude-sonnet-4-6"
    api_key: Optional[str] = None
    default_timeout_minutes: int = 30
    require_human_gates: bool = True
    # Which AIProvider backs codegen/review when not in mock_mode:
    # "anthropic" (default, one-shot API call) or "claude_code_cli"
    # (file-aware, iterative — shells out to the `claude` CLI).
    provider: str = "anthropic"

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
            ai_model=os.getenv("AI_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"),
            provider=os.getenv("AI_SD_OS_PROVIDER", "anthropic"),
        )
