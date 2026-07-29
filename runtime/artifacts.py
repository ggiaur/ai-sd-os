import hashlib
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Artifact(BaseModel):
    id: str
    artifact_type: str # source | test | doc | decision
    filepath: str
    version: str = "1.0.0"
    requirement_ref: Optional[str] = None
    checksum: str = ""
    timestamp: float = Field(default_factory=time.time)

class ArtifactRegistry:
    def __init__(self) -> None:
        self._artifacts: Dict[str, Artifact] = {}

    def register(self, artifact_id: str, artifact_type: str, filepath: str, content: str, req_ref: Optional[str] = None) -> Artifact:
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        art = Artifact(
            id=artifact_id,
            artifact_type=artifact_type,
            filepath=filepath,
            requirement_ref=req_ref,
            checksum=checksum
        )
        self._artifacts[artifact_id] = art
        return art

    def get(self, artifact_id: str) -> Optional[Artifact]:
        return self._artifacts.get(artifact_id)

    def list_artifacts(self) -> List[Artifact]:
        return list(self._artifacts.values())
