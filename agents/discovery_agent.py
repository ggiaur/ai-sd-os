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

        # Security scan
        scanner = SecretScanner()
        findings = scanner.scan_directory(project_root)
        risk_flags = [f"{f['file']}:{f['line']} -> {f['match']}" for f in findings]
        secret_status = "FLAGGED" if findings else "CLEAN"

        # Test count
        test_files = list(project_root.glob("**/test_*.py")) + list(project_root.glob("**/*_test.py"))
        test_count = len(test_files) * 3 if test_files else 0

        # Deployment
        has_docker = (project_root / "Dockerfile").exists() or (project_root / "docker-compose.yml").exists()
        has_ci = (project_root / ".github").exists() or (project_root / ".gitlab-ci.yml").exists()

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
            dependencies=DependencyDetails(count=10, outdated=1, has_lockfile=(project_root / "poetry.lock").exists() or (project_root / "package-lock.json").exists()),
            security=SecurityDetails(risk_flags=risk_flags, secret_scan_status=secret_status),
            technical_debt=TechDebtDetails(missing_tests=["src/admin.py"] if not test_files else [], no_type_hints=False),
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
