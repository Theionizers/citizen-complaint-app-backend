from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    description: str

class ComplaintStatusUpdate(BaseModel):
    status: str
class ComplaintResponse(BaseModel):
    id: int
    description: str
    status: str
    expected_resolution: str | None
    routing_confidence: float | None
    citizen_id: int
    department_id: int | None
    service_id: int | None
    assigned_officer_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplaintAssignment(BaseModel):
    officer_id: int