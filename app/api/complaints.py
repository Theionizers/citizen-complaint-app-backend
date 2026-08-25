from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models import Complaint, Department, Service, User
from app.schemas.complaint import ComplaintCreate, ComplaintResponse
from app.services.complaint_router import route_complaint

router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)


@router.post(
    "",
    response_model=ComplaintResponse
)
def create_complaint(
    data: ComplaintCreate,
    current_user: User = Depends(require_role("citizen")),
    db: Session = Depends(get_db)
):
    departments = db.query(Department).all()

    department_data = []

    for department in departments:
        services = (
            db.query(Service)
            .filter(Service.department_id == department.id)
            .all()
        )

        department_data.append({
            "department_id": department.id,
            "department_name": department.name,
            "services": [
                {
                    "service_id": service.id,
                    "service_name": service.name
                }
                for service in services
            ]
        })

    routing_result = route_complaint(
        data.description,
        department_data
    )

    department = (
        db.query(Department)
        .filter(
            Department.id == routing_result["department_id"]
        )
        .first()
    )

    service = (
        db.query(Service)
        .filter(
            Service.id == routing_result["service_id"],
            Service.department_id == routing_result["department_id"]
        )
        .first()
    )

    if department is None or service is None:
        raise ValueError("LLM returned invalid department or service")

    complaint = Complaint(
        description=data.description,
        status="submitted",
        expected_resolution=routing_result["expected_resolution"],
        routing_confidence=routing_result["routing_confidence"],
        citizen_id=current_user.id,
        department_id=department.id,
        service_id=service.id
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint

@router.get(
    "/my",
    response_model=list[ComplaintResponse]
)
def get_my_complaints(
    current_user: User = Depends(require_role("citizen")),
    db: Session = Depends(get_db)
):
    complaints = (
        db.query(Complaint)
        .filter(Complaint.citizen_id == current_user.id)
        .order_by(Complaint.created_at.desc())
        .all()
    )

    return complaints