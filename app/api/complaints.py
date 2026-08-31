from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models import Complaint, Department, Service, User,Role
from app.schemas.complaint import ComplaintCreate, ComplaintResponse,ComplaintStatusUpdate,ComplaintAssignment,AdminOfficerResponse
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

@router.get(
    "/officer",
    response_model=list[ComplaintResponse]
)
def get_officer_complaints(
    current_user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db)
):
    complaints = (
        db.query(Complaint)
        .filter(
            Complaint.department_id == current_user.department_id
        )
        .order_by(Complaint.created_at.desc())
        .all()
    )

    return complaints

@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintResponse
)
def update_complaint_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
    current_user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id,
            Complaint.department_id == current_user.department_id
        )
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    allowed_statuses = {
        "under_review",
        "in_progress",
        "resolved"
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid complaint status"
        )

    complaint.status = data.status

    db.commit()
    db.refresh(complaint)

    return complaint

@router.patch(
    "/{complaint_id}/assign",
    response_model=ComplaintResponse
)
def assign_complaint(
    complaint_id: int,
    data: ComplaintAssignment,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    officer = (
        db.query(User)
        .filter(
            User.id == data.officer_id,
            User.department_id == complaint.department_id
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=400,
            detail="Officer does not belong to complaint department"
        )

    complaint.assigned_officer_id = officer.id
    complaint.status = "assigned"

    db.commit()
    db.refresh(complaint)

    return complaint

@router.get(
    "/officer/assigned",
    response_model=list[ComplaintResponse]
)
def get_assigned_complaints(
    current_user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db)
):
    complaints = (
        db.query(Complaint)
        .filter(
            Complaint.assigned_officer_id == current_user.id
        )
        .order_by(Complaint.created_at.desc())
        .all()
    )

    return complaints


@router.get(
    "/admin",
    response_model=list[ComplaintResponse]
)
def get_all_complaints(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    complaints = (
        db.query(Complaint)
        .order_by(Complaint.created_at.desc())
        .all()
    )

    return complaints
@router.get(
    "/admin/officers",
    response_model=list[AdminOfficerResponse]
)
def get_admin_officers(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    officers = (
        db.query(User)
        .join(User.role)
        .filter(Role.name == "officer")
        .order_by(User.id.asc())
        .all()
    )

    return officers

@router.get(
    "/admin/{complaint_id}",
    response_model=ComplaintResponse
)
def get_admin_complaint(
    complaint_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(Complaint.id == complaint_id)
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint


