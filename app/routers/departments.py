from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Department, User
from app.schemas.schemas import DepartmentCreate, DepartmentRead
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentRead)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("admin", "hr_manager")),
):
    existing = db.query(Department).filter(Department.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Department code already exists")
    department = Department(**payload.model_dump())
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.get("/", response_model=list[DepartmentRead])
def list_departments(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(Department).order_by(Department.name.asc()).all()
