from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.db.database import get_db
from app.models import Complaint, Department, Service, User,Role
from app.schemas.complaint import ComplaintCreate, ComplaintResponse,ComplaintStatusUpdate,ComplaintAssignment,AdminOfficerResponse,OfficerDepartmentUpdate
from app.services.complaint_router import route_complaint
from app.services.transcription import transcribe_audio


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"]
)

PHOTOS_DIR = Path("uploads/complaints")
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _get_complaint_photo_dir(complaint_id: int) -> Path:
    complaint_dir = PHOTOS_DIR / str(complaint_id)
    complaint_dir.mkdir(parents=True, exist_ok=True)
    return complaint_dir


def _authorize_photo_access(
    complaint_id: int,
    current_user: User,
    db: Session,
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

    if current_user.role.name == "admin":
        return complaint

    if (
        current_user.role.name == "citizen"
        and complaint.citizen_id == current_user.id
    ):
        return complaint

    if (
        current_user.role.name == "officer"
        and complaint.assigned_officer_id == current_user.id
    ):
        return complaint

    raise HTTPException(
        status_code=403,
        detail="You are not allowed to view complaint photos"
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
        service_id=service.id,
        latitude=data.latitude,
        longitude=data.longitude,
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
        "in_progress"
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid complaint status"
        )

    if data.status == "in_progress":
        note = (data.officer_note or "").strip()
        if not note:
            raise HTTPException(
                status_code=400,
                detail="Officer note is required when moving a complaint to in_progress"
            )
        complaint.officer_note = note

    elif data.officer_note is not None:
        complaint.officer_note = data.officer_note.strip() or None

    complaint.status = data.status

    db.commit()
    db.refresh(complaint)

    return complaint


@router.patch(
    "/admin/{complaint_id}/status",
    response_model=ComplaintResponse
)
def update_admin_complaint_status(
    complaint_id: int,
    data: ComplaintStatusUpdate,
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

    if complaint.status == "closed":
        raise HTTPException(
            status_code=400,
            detail="Closed complaints cannot be updated"
        )

    allowed_statuses = {
        "under_review",
        "in_progress",
        "resolved",
        "closed"
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid complaint status"
        )

    if data.status == "closed" and complaint.status != "resolved":
        raise HTTPException(
            status_code=400,
            detail="A complaint must be resolved before it can be closed"
        )

    if data.status == "in_progress":
        note = (data.officer_note or "").strip()
        if not note:
            raise HTTPException(
                status_code=400,
                detail="Officer note is required when moving a complaint to in_progress"
            )
        complaint.officer_note = note
    elif data.officer_note is not None:
        complaint.officer_note = data.officer_note.strip() or None

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
    .join(User.role)
    .filter(
        User.id == data.officer_id,
        User.department_id == complaint.department_id,
        Role.name == "officer"
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
    "/admin/departments"
)
def get_admin_departments(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    departments = (
        db.query(Department)
        .order_by(Department.id.asc())
        .all()
    )

    return departments

@router.patch(
    "/admin/officers/{officer_id}/department"
)
def update_officer_department(
    officer_id: int,
    data: OfficerDepartmentUpdate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    officer = (
        db.query(User)
        .join(User.role)
        .filter(
            User.id == officer_id,
            Role.name == "officer"
        )
        .first()
    )

    if officer is None:
        raise HTTPException(
            status_code=404,
            detail="Officer not found"
        )

    department = (
        db.query(Department)
        .filter(Department.id == data.department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    officer.department_id = department.id

    db.commit()
    db.refresh(officer)

    return {
        "id": officer.id,
        "name": officer.name,
        "email": officer.email,
        "department_id": officer.department_id
    }

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

@router.post("/transcribe")
def transcribe_complaint_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(require_role("citizen")),
):
    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio filename is missing."
        )

    if not audio.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=415,
            detail="Only WAV audio files are currently supported."
        )

    try:
        transcription = transcribe_audio(audio.file)

        return {
            "text": transcription
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        print("Transcription error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"Audio transcription failed: {str(e)}"
        )

@router.post(
    "/{complaint_id}/photos",
    response_model=dict
)
async def upload_complaint_photos(
    complaint_id: int,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_role("citizen")),
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id,
            Complaint.citizen_id == current_user.id
        )
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one photo is required"
        )

    complaint_dir = _get_complaint_photo_dir(complaint_id)
    saved_files = []

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type for {file.filename or 'uploaded file'}"
            )

        original_extension = Path(file.filename or "").suffix.lower()

        if original_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file extension for {file.filename or 'uploaded file'}"
            )

        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Empty file: {file.filename or 'uploaded file'}"
            )

        saved_name = f"{uuid4().hex}{original_extension}"
        file_path = complaint_dir / saved_name
        file_path.write_bytes(file_bytes)
        saved_files.append(saved_name)

    return {
        "complaint_id": complaint_id,
        "uploaded_files": saved_files
    }


@router.get(
    "/{complaint_id}/photos",
    response_model=dict
)
def list_complaint_photos(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _authorize_photo_access(complaint_id, current_user, db)

    complaint_dir = _get_complaint_photo_dir(complaint_id)
    filenames = sorted(
        file.name
        for file in complaint_dir.iterdir()
        if file.is_file()
    )

    return {
        "complaint_id": complaint_id,
        "photos": [
            {
                "filename": filename,
                "url": f"/complaints/{complaint_id}/photos/{filename}"
            }
            for filename in filenames
        ]
    }


@router.get(
    "/{complaint_id}/photos/{filename}",
)
def get_complaint_photo(
    complaint_id: int,
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _authorize_photo_access(complaint_id, current_user, db)

    safe_filename = Path(filename).name

    if safe_filename != filename or safe_filename in {"", ".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid photo file name"
        )

    file_path = _get_complaint_photo_dir(complaint_id) / safe_filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Complaint photo not found"
        )

    return FileResponse(file_path)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse
)
def get_my_complaint(
    complaint_id: int,
    current_user: User = Depends(require_role("citizen")),
    db: Session = Depends(get_db)
):
    complaint = (
        db.query(Complaint)
        .filter(
            Complaint.id == complaint_id,
            Complaint.citizen_id == current_user.id
        )
        .first()
    )

    if complaint is None:
        raise HTTPException(
            status_code=404,
            detail="Complaint not found"
        )

    return complaint


