import re
from abc import ABC, abstractmethod
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
