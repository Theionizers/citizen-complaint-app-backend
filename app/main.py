from app.core.cors import setup_cors
from app.api.auth import router as auth_router
from fastapi import FastAPI
from app.api.rbac import router as rbac_router
from app.api.complaints import router as complaints_router
from app.core.cors import setup_cors
app = FastAPI(
    title="OZOCO AI Citizen Service Platform",
    version="1.0.0"
)

setup_cors(app)
@app.get("/")
def root():
    return {"message": "OZOCO API is running"}

app.include_router(auth_router)
app.include_router(rbac_router)
app.include_router(complaints_router)

from fastapi import APIRouter, Depends

from app.core.dependencies import require_role
from app.models import User

router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"]
)


@router.get("/citizen-test")
def citizen_test(
    current_user: User = Depends(require_role("citizen"))
):
    return {
        "message": "Citizen access granted",
        "user_id": current_user.id,
        "role": current_user.role.name
    }


@router.get("/officer-test")
def officer_test(
    current_user: User = Depends(require_role("officer"))
):
    return {
        "message": "Officer access granted",
        "user_id": current_user.id,
        "role": current_user.role.name
    }


@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_role("admin"))
):
    return {
        "message": "Admin access granted",
        "user_id": current_user.id,
        "role": current_user.role.name
    }

setup_cors(app)