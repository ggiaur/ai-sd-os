import time
import uuid
from typing import Any, Dict
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    """
    V6.1.0 Alap esemény séma (Event Schema Registry).
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    sender: str = "system"
