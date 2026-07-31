from pathlib import Path
from typing import Optional
from sdk.base_agent import BaseAgentSDK
from kernel.event_bus.events import Event, EventType
from contracts.codebase_snapshot import (
    CodebaseSnapshot, StackDetails, DependencyDetails,
    SecurityDetails, TechDebtDetails, TestQualityDetails, DeploymentDetails,
    InferredRequirement
)
from kernel.contracts.serializer import save_yaml_contract
from security.secret_scanner import SecretScanner

class DiscoveryAgent(BaseAgentSDK):
    def __init__(self, name: str, bus, provider, secret_scan_patterns: Optional[list] = None):
        self.secret_scan_patterns = secret_scan_patterns
        super().__init__(name, bus, provider)

    def register_subscriptions(self) -> None:
        self.bus.subscribe(EventType.SYSTEM_INITIALIZED, self.process_event)

    async def process_event(self, event: Event) -> None:
        pass

    async def survey_codebase(self, project_root: Path) -> CodebaseSnapshot:
        self.logger.info(f"Scanning codebase at {project_root}")

        languages = []
        frameworks = []
        databases = []

        if list(project_root.glob("*.py")) or list(project_root.glob("**/*.py")):
            languages.append("python")
        if list(project_root.glob("*.js")) or list(project_root.glob("*.ts")) or (project_root / "package.json").exists():
            languages.append("typescript/javascript")

        if (project_root / "requirements.txt").exists() or (project_root / "pyproject.toml").exists():
            req_content = ""
            for p in ["requirements.txt", "pyproject.toml"]:
                fpath = project_root / p
                if fpath.exists():
                    req_content += fpath.read_text(encoding="utf-8", errors="ignore")
            if "flask" in req_content.lower():
                frameworks.append("flask")
            if "fastapi" in req_content.lower():
                frameworks.append("fastapi")
            if "django" in req_content.lower():
                frameworks.append("django")
            if "sqlite" in req_content.lower():
                databases.append("sqlite")
            if "postgres" in req_content.lower() or "psycopg" in req_content.lower():
                databases.append("postgresql")

        # Security scan (kernel/policy/security.yaml alapján, ha be van kötve)
        scanner = SecretScanner(patterns=self.secret_scan_patterns)
        findings = scanner.scan_directory(project_root)
        risk_flags = [f"{f['file']}:{f['line']} -> {f['match']}" for f in findings]
        secret_status = "FLAGGED" if findings else "CLEAN"

        # Test count: count actual `def test_*` functions, not a made-up
        # per-file multiplier — a snapshot that fabricates numbers defeats the
        # entire point of "surveying" an existing codebase.
        test_files = list(project_root.glob("**/test_*.py")) + list(project_root.glob("**/*_test.py"))
        test_count = self._count_test_functions(test_files)

        # Deployment
        has_docker = (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists()
        has_ci = (project_root / ".github").exists() or (project_root / ".gitlab-ci.yml").exists()

        dep_count = self._count_dependencies(project_root)
        missing_tests = [] if test_files else ["No test_*.py / *_test.py files found anywhere in the project."]

        inferred = [
            InferredRequirement(
                id="FR-001",
                title="Kódbázis alapfunkciók",
                description="Felmért meglévő kódbázis modulok integrációja és tesztelése",
                confidence="HIGH",
                status="SATISFIED"
            )
        ]

        snapshot = CodebaseSnapshot(
            project_path=str(project_root.resolve()),
            stack=StackDetails(languages=languages or ["python"], frameworks=frameworks or ["standard"], databases=databases),
            architecture="monolith",
            dependencies=DependencyDetails(
                count=dep_count,
                # "outdated" would require querying PyPI/npm for latest versions —
                # Discovery deliberately does no network access, so we report 0
                # (unknown) rather than a plausible-looking made-up number.
                outdated=0,
                has_lockfile=(project_root / "poetry.lock").exists() or (project_root / "package-lock.json").exists(),
            ),
            security=SecurityDetails(risk_flags=risk_flags, secret_scan_status=secret_status),
            technical_debt=TechDebtDetails(missing_tests=missing_tests, no_type_hints=False),
            test_quality=TestQualityDetails(existing_tests_count=test_count, structural_only=False),
            deployment=DeploymentDetails(has_dockerfile=has_docker, has_ci_config=has_ci),
            inferred_requirements=inferred
        )

        ai_sd_dir = project_root / ".ai-sd-os"
        ai_sd_dir.mkdir(parents=True, exist_ok=True)
        save_yaml_contract(snapshot, ai_sd_dir / "CODEBASE_SNAPSHOT.yaml")

        await self.emit_event(
            event_type=EventType.CODEBASE_SURVEYED,
            payload={"snapshot": snapshot.model_dump(), "project_root": str(project_root)},
            correlation_id="discovery-init"
        )
        return snapshot

    @staticmethod
    def _count_test_functions(test_files: list) -> int:
        count = 0
        for f in test_files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for line in content.splitlines():
                if line.strip().startswith("def test_") or line.strip().startswith("async def test_"):
                    count += 1
        return count

    @staticmethod
    def _count_dependencies(project_root: Path) -> int:
        """Count real declared dependencies instead of reporting a fabricated number."""
        count = 0

        req_file = project_root / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    count += 1

        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                import json
                data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
                count += len(data.get("dependencies", {})) + len(data.get("devDependencies", {}))
            except (json.JSONDecodeError, OSError):
                pass

        return count
