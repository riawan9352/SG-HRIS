from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Employee, LeaveRequest, User
from app.schemas.schemas import LeaveApproval, LeaveRequestCreate, LeaveRequestRead
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/leave-requests", tags=["Leave Requests"])


@router.post("/", response_model=LeaveRequestRead)
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    leave_request = LeaveRequest(**payload.model_dump())
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


@router.patch("/{leave_id}/approval", response_model=LeaveRequestRead)
def approve_leave_request(
    leave_id: int,
    payload: LeaveApproval,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    leave_request.status = payload.status
    leave_request.approved_by = payload.approved_by
    db.commit()
    db.refresh(leave_request)
    return leave_request


@router.get("/", response_model=list[LeaveRequestRead])
def list_leave_requests(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(LeaveRequest).order_by(LeaveRequest.created_at.desc()).all()
