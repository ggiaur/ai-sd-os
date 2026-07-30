from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class StackDetails(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)

class DependencyDetails(BaseModel):
    count: int = 0
    outdated: int = 0
    has_lockfile: bool = False

class SecurityDetails(BaseModel):
    risk_flags: List[str] = Field(default_factory=list)
    secret_scan_status: str = "CLEAN"

class TechDebtDetails(BaseModel):
    missing_tests: List[str] = Field(default_factory=list)
    no_type_hints: bool = False

class TestQualityDetails(BaseModel):
    existing_tests_count: int = 0
    structural_only: bool = False

class DeploymentDetails(BaseModel):
    has_dockerfile: bool = False
    has_ci_config: bool = False

class InferredRequirement(BaseModel):
    id: str
    title: str
    description: str
    confidence: str = "HIGH"
    status: str = "PENDING"

class CodebaseSnapshot(BaseModel):
    project_path: str
    stack: StackDetails = Field(default_factory=StackDetails)
    architecture: str = "monolith"
    dependencies: DependencyDetails = Field(default_factory=DependencyDetails)
    security: SecurityDetails = Field(default_factory=SecurityDetails)
    technical_debt: TechDebtDetails = Field(default_factory=TechDebtDetails)
    test_quality: TestQualityDetails = Field(default_factory=TestQualityDetails)
    deployment: DeploymentDetails = Field(default_factory=DeploymentDetails)
    inferred_requirements: List[InferredRequirement] = Field(default_factory=list)
