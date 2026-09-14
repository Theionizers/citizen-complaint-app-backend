import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.database import get_db
from app.models import Role, User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyOTPRequest,
    ResendOTPRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.email_service import send_email


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

limiter = Limiter(key_func=get_remote_address)


def generate_otp() -> str:
    """Generate a secure six-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def build_otp_email(name: str, otp: str) -> str:
    return f"""
    <html>
        <body>
            <h2>Verify your OZOCO account</h2>

            <p>Hello {name},</p>

            <p>
                Thank you for registering with OZOCO.
                Use the following OTP to verify your email address:
            </p>

            <h1 style="
                letter-spacing: 8px;
                color: #2563eb;
                font-size: 36px;
            ">
                {otp}
            </h1>

            <p>
                This OTP will expire in
                {settings.EMAIL_OTP_EXPIRE_MINUTES} minutes.
            </p>

            <p>
                If you did not create an OZOCO account,
                you can ignore this email.
            </p>
        </body>
    </html>
    """


def build_password_reset_email(name: str, otp: str) -> str:
    return f"""
    <html>
        <body>
            <h2>OZOCO Password Reset</h2>

            <p>Hello {name},</p>

            <p>
                We received a request to reset your OZOCO password.
                Use the following OTP to continue:
            </p>

            <h1 style="
                letter-spacing: 8px;
                color: #dc2626;
                font-size: 36px;
            ">
                {otp}
            </h1>

            <p>
                This OTP will expire in
                {settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES} minutes.
            </p>

            <p>
                If you did not request a password reset,
                you can safely ignore this email.
            </p>
        </body>
    </html>
    """


@router.post("/register")
@limiter.limit("5/minute")
def register(
    request: Request,
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    citizen_role = (
        db.query(Role)
        .filter(Role.name == "citizen")
        .first()
    )

    if citizen_role is None:
        raise HTTPException(
            status_code=500,
            detail="Citizen role not configured",
        )

    otp = generate_otp()
    now = datetime.utcnow()

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=citizen_role.id,
        is_email_verified=False,
        email_otp_hash=hash_token(otp),
        email_otp_expires_at=(
            now + timedelta(
                minutes=settings.EMAIL_OTP_EXPIRE_MINUTES
            )
        ),
        email_otp_attempts=0,
        email_otp_last_sent_at=now,
    )

    db.add(user)

    email_html = build_otp_email(
        name=data.name,
        otp=otp,
    )

    try:
        db.flush()

        send_email(
            to_email=data.email,
            subject="Your OZOCO email verification OTP",
            html=email_html,
        )

        db.commit()
        db.refresh(user)

    except Exception as error:
        db.rollback()
        print("OTP EMAIL ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to send verification OTP",
        )

    return {
        "message": "Registration successful. OTP sent to your email.",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": citizen_role.name,
        "requires_email_verification": True,
    }


@router.post("/verify-otp")
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    data: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid email or OTP",
        )

    if user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified",
        )

    if (
        user.email_otp_hash is None
        or user.email_otp_expires_at is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No active OTP. Please request a new OTP.",
        )

    if user.email_otp_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please request a new OTP.",
        )

    if user.email_otp_attempts >= settings.EMAIL_OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Maximum OTP attempts exceeded. Please request a new OTP.",
        )

    if not data.otp.isdigit() or len(data.otp) != 6:
        raise HTTPException(
            status_code=400,
            detail="OTP must contain exactly six digits",
        )

    if not secrets.compare_digest(
        hash_token(data.otp),
        user.email_otp_hash,
    ):
        user.email_otp_attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid OTP",
        )

    user.is_email_verified = True
    user.email_otp_hash = None
    user.email_otp_expires_at = None
    user.email_otp_attempts = 0
    user.email_otp_last_sent_at = None

    db.commit()

    return {
        "message": "Email verified successfully",
    }


@router.post("/resend-otp")
@limiter.limit("3/10minutes")
def resend_otp(
    request: Request,
    data: ResendOTPRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified",
        )

    now = datetime.utcnow()

    if user.email_otp_last_sent_at is not None:
        elapsed_seconds = (
            now - user.email_otp_last_sent_at
        ).total_seconds()

        if elapsed_seconds < settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS:
            remaining_seconds = max(
                1,
                int(
                    settings.EMAIL_OTP_RESEND_COOLDOWN_SECONDS
                    - elapsed_seconds
                ),
            )

            raise HTTPException(
                status_code=429,
                detail=(
                    f"Please wait {remaining_seconds} seconds "
                    "before requesting another OTP"
                ),
            )

    otp = generate_otp()

    user.email_otp_hash = hash_token(otp)
    user.email_otp_expires_at = (
        now + timedelta(
            minutes=settings.EMAIL_OTP_EXPIRE_MINUTES
        )
    )
    user.email_otp_attempts = 0
    user.email_otp_last_sent_at = now

    email_html = build_otp_email(
        name=user.name,
        otp=otp,
    )

    try:
        db.flush()

        send_email(
            to_email=user.email,
            subject="Your new OZOCO verification OTP",
            html=email_html,
        )

        db.commit()

    except Exception as error:
        db.rollback()
        print("RESEND OTP ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to resend verification OTP",
        )

    return {
        "message": "A new OTP has been sent to your email",
    }


@router.post("/forgot-password")
@limiter.limit("3/10minutes")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    generic_response = {
        "message": (
            "If an account exists with this email, "
            "a password reset OTP has been sent."
        )
    }

    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        return generic_response

    now = datetime.utcnow()

    if user.password_reset_otp_last_sent_at is not None:
        elapsed_seconds = (
            now - user.password_reset_otp_last_sent_at
        ).total_seconds()

        if (
            elapsed_seconds
            < settings.PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS
        ):
            return generic_response

    otp = generate_otp()

    user.password_reset_otp_hash = hash_token(otp)
    user.password_reset_otp_expires_at = (
        now + timedelta(
            minutes=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES
        )
    )
    user.password_reset_otp_attempts = 0
    user.password_reset_otp_last_sent_at = now

    try:
        db.flush()

        send_email(
            to_email=user.email,
            subject="Your OZOCO password reset OTP",
            html=build_password_reset_email(
                name=user.name,
                otp=otp,
            ),
        )

        db.commit()

    except Exception as error:
        db.rollback()
        print("PASSWORD RESET EMAIL ERROR:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to send password reset OTP",
        )

    return generic_response


@router.post("/reset-password")
@limiter.limit("10/minute")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    if (
        user.password_reset_otp_hash is None
        or user.password_reset_otp_expires_at is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    if (
        user.password_reset_otp_attempts
        >= settings.PASSWORD_RESET_OTP_MAX_ATTEMPTS
    ):
        raise HTTPException(
            status_code=429,
            detail="Maximum password reset OTP attempts exceeded",
        )

    now = datetime.utcnow()

    if now > user.password_reset_otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    if not data.otp.isdigit() or len(data.otp) != 6:
        raise HTTPException(
            status_code=400,
            detail="OTP must contain exactly six digits",
        )

    if not secrets.compare_digest(
        hash_token(data.otp),
        user.password_reset_otp_hash,
    ):
        user.password_reset_otp_attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    user.password_hash = hash_password(data.new_password)

    user.password_reset_otp_hash = None
    user.password_reset_otp_expires_at = None
    user.password_reset_otp_attempts = 0
    user.password_reset_otp_last_sent_at = None

    db.commit()

    return {
        "message": "Password reset successfully",
    }


@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in",
        )

    access_token = create_access_token(
        user_id=user.id,
        role=user.role.name,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name,
    }