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