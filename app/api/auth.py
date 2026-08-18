from fastapi import APIRouter
from app.schemas.auth import RegisterRequest

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register")
def register(data: RegisterRequest):
    return {
        "message": "Registration endpoint working",
        "email": data.email
    }