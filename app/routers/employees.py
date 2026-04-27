from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Department, Employee, User
from app.schemas.schemas import EmployeeCreate, EmployeeRead
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("/", response_model=EmployeeRead)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Department).filter(Department.id == payload.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")
    existing = db.query(Employee).filter(Employee.employee_id == payload.employee_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/", response_model=list[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(Employee).order_by(Employee.last_name.asc()).all()
