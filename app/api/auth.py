from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models import Role, User
from app.db.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
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

    citizen_role = (
        db.query(Role)
        .filter(Role.name == "citizen")
        .first()
    )

    if citizen_role is None:
        raise HTTPException(
            status_code=500,
            detail="Citizen role not configured"
        )

    password_hash = hash_password(data.password)

    user = User(
        name=data.name,
        email=data.email,
        password_hash=password_hash,
        role_id=citizen_role.id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": citizen_role.name
    }