from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Department, TrainingNeedAnalysis, User
from app.schemas.schemas import (
    TrainingNeedAnalysisCreate,
    TrainingNeedAnalysisRead,
    TrainingNeedAnalysisUpdate,
    TrainingNeedAnalysisVerify,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/training-needs", tags=["Training Needs Analysis"])


@router.post("/", response_model=TrainingNeedAnalysisRead)
def create_training_need(
    payload: TrainingNeedAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "hr_manager")),
):
    if payload.department_id is not None:
        department = db.query(Department).filter(Department.id == payload.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
    item = TrainingNeedAnalysis(
        **payload.model_dump(),
        created_by=current_user.username,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=list[TrainingNeedAnalysisRead])
def list_training_needs(
    workforce_category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(TrainingNeedAnalysis)
    if workforce_category:
        query = query.filter(TrainingNeedAnalysis.workforce_category == workforce_category)
    if status:
        query = query.filter(TrainingNeedAnalysis.status == status)
    return query.order_by(TrainingNeedAnalysis.created_at.desc()).all()


@router.patch("/{analysis_id}", response_model=TrainingNeedAnalysisRead)
def update_training_need(
    analysis_id: int,
    payload: TrainingNeedAnalysisUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(TrainingNeedAnalysis).filter(TrainingNeedAnalysis.id == analysis_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Training need analysis not found")

    updates = payload.model_dump(exclude_unset=True)
    if "department_id" in updates and updates["department_id"] is not None:
        department = db.query(Department).filter(Department.id == updates["department_id"]).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{analysis_id}/verify", response_model=TrainingNeedAnalysisRead)
def verify_training_need(
    analysis_id: int,
    payload: TrainingNeedAnalysisVerify,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(TrainingNeedAnalysis).filter(TrainingNeedAnalysis.id == analysis_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Training need analysis not found")
    item.status = payload.status
    item.verified_by = payload.verified_by
    item.verified_at = datetime.utcnow()
    item.verification_notes = payload.verification_notes
    db.commit()
    db.refresh(item)
    return item
