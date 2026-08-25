from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.database import get_db
from app.models import Complaint, User
from app.schemas.complaint import ComplaintCreate, ComplaintResponse

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
    complaint = Complaint(
        description=data.description,
        citizen_id=current_user.id,
        status="submitted"
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return complaint