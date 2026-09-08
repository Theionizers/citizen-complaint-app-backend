from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.core.security import hash_password
from app.db.database import get_db
from app.models import Department, Role, User
from app.schemas.auth import OfficerCreate

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.post("/officers")
def create_officer(
    data: OfficerCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    # Check email
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Verify department
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

    # Get officer role
    officer_role = (
        db.query(Role)
        .filter(Role.name == "officer")
        .first()
    )

    if officer_role is None:
        raise HTTPException(
            status_code=500,
            detail="Officer role not configured"
        )

    officer = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=officer_role.id,
        department_id=department.id
    )

    db.add(officer)
    db.commit()
    db.refresh(officer)

    return {
        "message": "Officer created successfully",
        "officer": {
            "id": officer.id,
            "name": officer.name,
            "email": officer.email,
            "department_id": officer.department_id,
            "role": officer_role.name
        }
    }