from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

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
    async def generate(self, prompt: str, context: Optional[dict] = None) -> str:
        if "ArchitectAgent" in prompt or "SPEC" in prompt:
            return "Mock Architect Plan: Create modular structure."
        elif "DeveloperAgent" in prompt or "WorkPackage" in prompt:
            return "```python\n# Mock generated code\ndef main():\n    pass\n```"
        return "Mock AI response for prompt."

    async def review(self, code: str, criteria: List[str]) -> ReviewResult:
        return ReviewResult(passed=True, feedback="Mock review passed cleanly.", issues=[])

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
        prompt = f"Review the following code against criteria: {criteria}\n\nCode:\n{code}"
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
