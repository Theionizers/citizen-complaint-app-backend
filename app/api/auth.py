from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.database import get_db
from app.models import Role, User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.email_service import send_email


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

    verification_token = generate_secure_token()
    verification_token_hash = hash_token(verification_token)

    verification_expires_at = (
        datetime.utcnow()
        + timedelta(
            minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
    )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=password_hash,
        role_id=citizen_role.id,
        is_email_verified=False,
        email_verification_token_hash=verification_token_hash,
        email_verification_expires_at=verification_expires_at,
    )

    db.add(user)

    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email"
        f"?token={verification_token}"
    )

    email_html = f"""
    <html>
        <body>
            <h2>Verify your OZOCO account</h2>

            <p>Hello {user.name},</p>

            <p>
                Thank you for registering with OZOCO.
                Please verify your email address by clicking
                the button below.
            </p>

            <p>
                <a
                    href="{verification_link}"
                    style="
                        display:inline-block;
                        padding:10px 20px;
                        background:#2563eb;
                        color:white;
                        text-decoration:none;
                        border-radius:5px;
                    "
                >
                    Verify Email
                </a>
            </p>

            <p>
                This verification link will expire in
                {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES}
                minutes.
            </p>

            <p>
                If you did not create an OZOCO account,
                you can ignore this email.
            </p>
        </body>
    </html>
    """

    try:
        send_email(
            to_email=user.email,
            subject="Verify your OZOCO email address",
            html=email_html,
        )

        db.commit()
        db.refresh(user)

    except Exception as e:
        db.rollback()
        print("EMAIL VERIFICATION ERROR:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Unable to send verification email"
        )

    return {
        "message": "Registration successful. Please verify your email.",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": citizen_role.name
    }


@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    token_hash = hash_token(token)

    user = (
        db.query(User)
        .filter(
            User.email_verification_token_hash == token_hash
        )
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    if user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    if (
        user.email_verification_expires_at is None
        or user.email_verification_expires_at < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )

    user.is_email_verified = True
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None

    db.commit()

    return {
        "message": "Email verified successfully"
    }


@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in"
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role.name
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name
    }