from pydantic import BaseModel, Field

class Retrospective(BaseModel):
    sprint_id: str
    what_worked: str
    what_failed: str
    carry_forward_note: str
    retry_count: int = 0
    duration_minutes: int = 0
