"""Role-specific portal endpoints. Each one is restricted to a single role."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.models import Role, User

router = APIRouter()


@router.get("/student")
def student_portal(user: User = Depends(require_roles(Role.student))):
    s = user.student
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return {
        "full_name": user.full_name,
        "roll_number": s.roll_number,
        "department": s.department,
        "priority_category": s.priority_category,
        "turns_completed": s.turns_completed,
        "turns_missed": s.turns_missed,
    }


@router.get("/staff")
def staff_portal(user: User = Depends(require_roles(Role.staff))):
    s = user.staff
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    return {
        "full_name": user.full_name,
        "employee_code": s.employee_code,
        "designation": s.designation,
        "is_available": s.is_available,
    }


@router.get("/admin")
def admin_portal(
    user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    rows = db.execute(select(User.role, func.count(User.id)).group_by(User.role)).all()
    return {
        "full_name": user.full_name,
        "users_by_role": {role.value: count for role, count in rows},
    }
