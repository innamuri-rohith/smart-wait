"""Registration, login, and current-user endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import Role, Student, User
from app.schemas.auth import LoginRequest, StudentRegister, TokenResponse, UserOut

router = APIRouter()


@router.post("/register/student", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegister, db: Session = Depends(get_db)):
    email = payload.email.lower()

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    if db.scalar(select(Student).where(Student.roll_number == payload.roll_number)):
        raise HTTPException(status_code=409, detail="Roll number already registered")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=Role.student,
    )
    user.student = Student(roll_number=payload.roll_number, department=payload.department)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Account already exists")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    # Same message for unknown email and wrong password, so accounts cannot be enumerated.
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(user.id), role=user.role)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
