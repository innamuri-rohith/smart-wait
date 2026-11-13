"""Administrator-only endpoints: staff management and user listing."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.db.database import get_db
from app.db.models import Role, Staff, User
from app.schemas.auth import StaffCreate, UserOut

router = APIRouter()


@router.post("/staff", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.admin)),
):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.scalar(select(Staff).where(Staff.employee_code == payload.employee_code)):
        raise HTTPException(status_code=409, detail="Employee code already exists")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=Role.staff,
    )
    user.staff = Staff(employee_code=payload.employee_code, designation=payload.designation)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Staff account already exists")
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles(Role.admin)),
):
    return db.scalars(select(User).order_by(User.id)).all()
