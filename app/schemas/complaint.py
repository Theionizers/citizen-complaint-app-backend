from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComplaintCreate(BaseModel):
    description: str
    latitude: float | None = None
    longitude: float | None = None

class ComplaintStatusUpdate(BaseModel):
    status: str
    officer_note: str | None = None

class ComplaintResponse(BaseModel):
    id: int
    description: str
    status: str
    expected_resolution: str | None
    routing_confidence: float | None
    citizen_id: int
    department_id: int | None
    service_id: int | None
    officer_note: str | None
    assigned_officer_id: int | None
    created_at: datetime
    updated_at: datetime
    latitude: float | None
    longitude: float | None

    model_config = ConfigDict(from_attributes=True)


class ComplaintAssignment(BaseModel):
    officer_id: int

class AdminOfficerResponse(BaseModel):
    id: int
    name: str
    email: str
    department_id: int | None

    model_config = ConfigDict(from_attributes=True)

class OfficerDepartmentUpdate(BaseModel):
    department_id: int