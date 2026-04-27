from fastapi import APIRouter, Depends, HTTPException
from datetime import date
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Candidate, Department, Employee, OnboardingTask, RecruitmentPosition, User
from app.schemas.schemas import (
    CandidateCreate,
    CandidateRead,
    CandidateStageUpdate,
    OnboardingTaskCreate,
    OnboardingTaskRead,
    OnboardingTaskUpdate,
    RecruitmentAnalyticsSummary,
    RecruitmentPositionCreate,
    RecruitmentPositionRead,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/recruitment", tags=["Recruitment & Talent Management"])


@router.post("/positions", response_model=RecruitmentPositionRead)
def create_position(
    payload: RecruitmentPositionCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Department).filter(Department.id == payload.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")
    item = RecruitmentPosition(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/positions", response_model=list[RecruitmentPositionRead])
def list_positions(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(RecruitmentPosition).order_by(RecruitmentPosition.open_date.desc()).all()


@router.post("/candidates", response_model=CandidateRead)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    if not db.query(RecruitmentPosition).filter(RecruitmentPosition.id == payload.position_id).first():
        raise HTTPException(status_code=404, detail="Recruitment position not found")
    item = Candidate(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/candidates/{candidate_id}", response_model=CandidateRead)
def update_candidate_stage(
    candidate_id: int,
    payload: CandidateStageUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Candidate not found")
    item.stage = payload.stage
    item.status = payload.status
    item.score = payload.score
    db.commit()
    db.refresh(item)
    return item


@router.get("/candidates", response_model=list[CandidateRead])
def list_candidates(
    position_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(Candidate)
    if position_id is not None:
        query = query.filter(Candidate.position_id == position_id)
    return query.order_by(Candidate.id.desc()).all()


@router.post("/onboarding/tasks", response_model=OnboardingTaskRead)
def create_onboarding_task(
    payload: OnboardingTaskCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    item = OnboardingTask(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/onboarding/tasks/{task_id}", response_model=OnboardingTaskRead)
def update_onboarding_task(
    task_id: int,
    payload: OnboardingTaskUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Onboarding task not found")
    item.status = payload.status
    item.notes = payload.notes
    db.commit()
    db.refresh(item)
    return item


@router.get("/onboarding/tasks", response_model=list[OnboardingTaskRead])
def list_onboarding_tasks(
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(OnboardingTask)
    if employee_id is not None:
        query = query.filter(OnboardingTask.employee_id == employee_id)
    return query.order_by(OnboardingTask.id.desc()).all()


@router.get("/analytics/summary", response_model=RecruitmentAnalyticsSummary)
def recruitment_analytics_summary(
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    open_positions = db.query(RecruitmentPosition).filter(RecruitmentPosition.status == "open").count()
    active_candidates = db.query(Candidate).filter(Candidate.status == "active").count()
    hired_candidates = db.query(Candidate).filter(Candidate.status == "hired").count()
    rejected_candidates = db.query(Candidate).filter(Candidate.status == "rejected").count()

    total_processed = hired_candidates + rejected_candidates
    conversion_rate = round((hired_candidates / total_processed) * 100) if total_processed > 0 else 0

    today = date.today()
    onboarding_total = db.query(OnboardingTask).count()
    onboarding_completed = db.query(OnboardingTask).filter(OnboardingTask.status == "done").count()
    onboarding_overdue = (
        db.query(OnboardingTask)
        .filter(OnboardingTask.status != "done")
        .filter(OnboardingTask.due_date.isnot(None))
        .filter(OnboardingTask.due_date < today)
        .count()
    )
    onboarding_sla = round((onboarding_completed / onboarding_total) * 100) if onboarding_total > 0 else 100

    return RecruitmentAnalyticsSummary(
        total_open_positions=open_positions,
        total_active_candidates=active_candidates,
        candidates_hired=hired_candidates,
        candidates_rejected=rejected_candidates,
        conversion_rate_percent=conversion_rate,
        onboarding_total_tasks=onboarding_total,
        onboarding_overdue_tasks=onboarding_overdue,
        onboarding_completed_tasks=onboarding_completed,
        onboarding_sla_percent=onboarding_sla,
    )
