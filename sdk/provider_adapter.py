import asyncio
import re
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from security.secret_scanner import SecretScanner

_TASK_LINE_RE = re.compile(
    r"fn_name:\s*(\w+)\s*\|\s*requirement:\s*(\S+)\s*\|\s*task:\s*(.*?)\s*\|\s*must return exactly:\s*'(.*?)'"
)

_DANGEROUS_CODE_PATTERNS = [
    (re.compile(r"\beval\s*\("), "uses eval()"),
    (re.compile(r"\bexec\s*\("), "uses exec()"),
    (re.compile(r"os\.system\s*\("), "shells out via os.system()"),
    (re.compile(r"subprocess\.\w+\([^)]*shell\s*=\s*True"), "runs a subprocess with shell=True"),
]


def _independent_code_review(code: str) -> ReviewResult:
    """Shared, deterministic reviewer logic used by MockProviderAdapter.

    This is deliberately NOT the same code path as `generate()` — it looks for
    a different class of problem (secrets, dangerous execution patterns) than
    "does the acceptance test pass". A reviewer that only re-checks the same
    thing the implementer already satisfied isn't an independent second
    opinion, it's theater.
    """
    issues: List[str] = []

    for finding in SecretScanner().scan_text(code, source_label="<reviewed-code>"):
        issues.append(f"Possible hardcoded secret at line {finding['line']}: {finding['match']}")

    for pattern, description in _DANGEROUS_CODE_PATTERNS:
        if pattern.search(code):
            issues.append(f"Dangerous pattern: {description}")

    if issues:
        return ReviewResult(passed=False, feedback="; ".join(issues), issues=issues)
    return ReviewResult(passed=True, feedback="No secrets or dangerous execution patterns found.", issues=[])

class ReviewResult(BaseModel):
    passed: bool
    feedback: str = ""
    issues: List[str] = []

class AnalysisResult(BaseModel):
    summary: str
    key_findings: List[str] = []
    metadata: Dict[str, Any] = {}

class AIProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        pass

    @abstractmethod
    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def analyze(self, artifact: str) -> AnalysisResult:
        pass

class MockProviderAdapter(AIProvider):
    """Deterministic stand-in for a real LLM.

    For DeveloperAgent-style prompts (see agents/developer_agent.py._build_prompt),
    it actually parses the requested fn_name / expected-return contract and emits
    matching implementations — it does not know about the acceptance tests
    ArchitectAgent already wrote, so this still exercises a genuine (if trivial)
    codegen -> independent-verification path instead of being a hardcoded template
    shared between "implementation" and "test".
    """

    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        task_matches = _TASK_LINE_RE.findall(prompt)
        if task_matches:
            body = "\n\n".join(
                f"def {fn_name}():\n    return {expected!r}"
                for fn_name, _req, _desc, expected in task_matches
            )
            return f"```python\n{body}\n```"
        if "ArchitectAgent" in prompt or "SPEC" in prompt:
            return "Mock Architect Plan: Create modular structure."
        elif "DeveloperAgent" in prompt or "WorkPackage" in prompt:
            return "```python\n# Mock generated code\ndef main():\n    pass\n```"
        return "Mock AI response for prompt."

    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        return _independent_code_review(code)

    async def embed(self, text: str) -> List[float]:
        return [0.0] * 1536

    async def analyze(self, artifact: str) -> AnalysisResult:
        return AnalysisResult(summary="Mock analysis", key_findings=["All clear"], metadata={})

class AnthropicAdapter(AIProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            resp = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.content[0].text
        except Exception as e:
            return f"[Anthropic Fallback Mock Output due to error: {e}]"

    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        # Deterministic backstop first: secrets and dangerous execution
        # patterns must never depend solely on an LLM's judgment call.
        deterministic = _independent_code_review(code)
        if not deterministic.passed:
            return deterministic

        prompt = (
            "You are an INDEPENDENT senior QA engineer reviewing code written by a "
            "different developer. You did not write this code and have no stake in "
            "it being accepted — be skeptical, not agreeable. Reply with the single "
            "word PASSED only if the code genuinely satisfies every criterion below; "
            "otherwise reply FAILED followed by a one-line reason.\n\n"
            f"Criteria:\n" + "\n".join(f"- {c}" for c in criteria) + f"\n\nCode:\n{code}"
        )
        res = await self.generate(prompt)
        return ReviewResult(passed="PASSED" in res.upper(), feedback=res)

    async def embed(self, text: str) -> List[float]:
        return [0.0] * 1536

    async def analyze(self, artifact: str) -> AnalysisResult:
        res = await self.generate(f"Analyze the following artifact:\n{artifact}")
        return AnalysisResult(summary=res, key_findings=[res])

class ClaudeCodeCLIAdapter(AIProvider):
    """Shells out to the Claude Code CLI itself as the codegen backend.

    Unlike AnthropicAdapter (one text-in/text-out API call, blind to the
    surrounding project), this gives the "developer" a real, file-aware,
    iterative coding agent: it can read the project it's working in, run
    commands, and self-correct — the same kind of session driving this
    conversation, just invoked non-interactively and scoped to one prompt.

    Model: whatever `model` is set to (default: the engine's configured
    `KernelConfig.ai_model`, e.g. "claude-sonnet-4-6") — passed straight
    through to `claude --model`. Nothing is hardcoded here; the model choice
    lives in one place (KernelConfig), same as every other provider.
    """

    def __init__(
        self,
        model: str,
        cwd: Path,
        permission_mode: str = "acceptEdits",
        timeout_seconds: int = 600,
    ):
        self.model = model
        self.cwd = Path(cwd)
        self.permission_mode = permission_mode
        self.timeout_seconds = timeout_seconds

    def _run_cli_sync(self, prompt: str) -> str:
        cmd = [
            "claude", "-p", prompt,
            "--model", self.model,
            "--output-format", "text",
            "--permission-mode", self.permission_mode,
        ]
        try:
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "The 'claude' CLI was not found on PATH. Install Claude Code, or "
                "select a different provider (mock/anthropic) in KernelConfig."
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"claude CLI timed out after {self.timeout_seconds}s for this prompt."
            ) from e

        if result.returncode != 0:
            raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr[:2000]}")
        return result.stdout

    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        # subprocess.run is blocking; run it off the event loop thread so it
        # doesn't stall the rest of the async pipeline (HITL prompts, other
        # agents' event handling) while a CLI session is working.
        return await asyncio.to_thread(self._run_cli_sync, prompt)

    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        # Same deterministic backstop as AnthropicAdapter: secrets and
        # dangerous execution patterns are never left to an LLM's judgment call.
        deterministic = _independent_code_review(code)
        if not deterministic.passed:
            return deterministic

        prompt = (
            "You are an INDEPENDENT senior QA engineer reviewing code written by a "
            "different session. You did not write this code — be skeptical, not "
            "agreeable. Reply with the single word PASSED only if the code genuinely "
            "satisfies every criterion below; otherwise reply FAILED followed by a "
            "one-line reason.\n\n"
            f"Criteria:\n" + "\n".join(f"- {c}" for c in criteria) + f"\n\nCode:\n{code}"
        )
        res = await self.generate(prompt)
        return ReviewResult(passed="PASSED" in res.upper(), feedback=res)

    async def embed(self, text: str) -> List[float]:
        raise NotImplementedError(
            "ClaudeCodeCLIAdapter does not support embeddings — use AnthropicAdapter "
            "(or a dedicated embeddings provider) for RAG/search features."
        )

    async def analyze(self, artifact: str) -> AnalysisResult:
        res = await self.generate(f"Analyze the following artifact and summarize key findings:\n{artifact}")
        return AnalysisResult(summary=res, key_findings=[res])


class OpenAIAdapter(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        return f"[OpenAI output mock for model {self.model}]"

    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        return ReviewResult(passed=True, feedback="OpenAI review passed.")

    async def embed(self, text: str) -> List[float]:
        return [0.0] * 1536

    async def analyze(self, artifact: str) -> AnalysisResult:
        return AnalysisResult(summary="OpenAI analysis", key_findings=[])
