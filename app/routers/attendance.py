from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import AttendanceRecord, Employee, OvertimeRecord, ShiftSchedule, User
from app.schemas.schemas import (
    AttendanceCreate,
    AttendanceRead,
    OvertimeApproval,
    OvertimeCreate,
    OvertimeRead,
    ShiftScheduleCreate,
    ShiftScheduleRead,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/attendance", tags=["Attendance & Time Tracking"])


@router.post("/records", response_model=AttendanceRead)
def create_attendance_record(
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    item = AttendanceRecord(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/records", response_model=list[AttendanceRead])
def list_attendance_records(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(AttendanceRecord)
    if employee_id is not None:
        query = query.filter(AttendanceRecord.employee_id == employee_id)
    return query.order_by(AttendanceRecord.attendance_date.desc()).all()


@router.post("/shifts", response_model=ShiftScheduleRead)
def create_shift_schedule(
    payload: ShiftScheduleCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    item = ShiftSchedule(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/shifts", response_model=list[ShiftScheduleRead])
def list_shift_schedules(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(ShiftSchedule)
    if employee_id is not None:
        query = query.filter(ShiftSchedule.employee_id == employee_id)
    return query.order_by(ShiftSchedule.shift_date.desc()).all()


@router.post("/overtime", response_model=OvertimeRead)
def create_overtime_request(
    payload: OvertimeCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    item = OvertimeRecord(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/overtime/{overtime_id}/approval", response_model=OvertimeRead)
def approve_overtime_request(
    overtime_id: int,
    payload: OvertimeApproval,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(OvertimeRecord).filter(OvertimeRecord.id == overtime_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Overtime record not found")
    item.status = payload.status
    item.approved_by = payload.approved_by
    db.commit()
    db.refresh(item)
    return item


@router.get("/overtime", response_model=list[OvertimeRead])
def list_overtime_records(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(OvertimeRecord).order_by(OvertimeRecord.overtime_date.desc()).all()
