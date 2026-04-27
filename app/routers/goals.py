from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Employee, EmployeeGoal, KpiDefinition, KpiReview, User
from app.schemas.schemas import (
    EmployeeGoalCreate,
    EmployeeGoalRead,
    EmployeeGoalUpdate,
    GoalKpiCalibrationSummary,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/goals", tags=["Goal Tracking"])


@router.post("/", response_model=EmployeeGoalRead)
def create_goal(
    payload: EmployeeGoalCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.linked_kpi_id is not None and not db.query(KpiDefinition).filter(KpiDefinition.id == payload.linked_kpi_id).first():
        raise HTTPException(status_code=404, detail="Linked KPI not found")
    item = EmployeeGoal(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{goal_id}", response_model=EmployeeGoalRead)
def update_goal_progress(
    goal_id: int,
    payload: EmployeeGoalUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    item = db.query(EmployeeGoal).filter(EmployeeGoal.id == goal_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Goal not found")
    item.current_value = payload.current_value
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=list[EmployeeGoalRead])
def list_goals(
    employee_id: int | None = None,
    review_period: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(EmployeeGoal)
    if employee_id is not None:
        query = query.filter(EmployeeGoal.employee_id == employee_id)
    if review_period is not None:
        query = query.filter(EmployeeGoal.review_period == review_period)
    return query.order_by(EmployeeGoal.created_at.desc()).all()


@router.get("/calibration-summary", response_model=GoalKpiCalibrationSummary)
def goal_kpi_calibration_summary(
    department_id: int,
    review_period: str,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    employee_ids = [
        row.id for row in db.query(Employee).filter(Employee.department_id == department_id).all()
    ]
    goals = (
        db.query(EmployeeGoal)
        .filter(EmployeeGoal.review_period == review_period)
        .filter(EmployeeGoal.employee_id.in_(employee_ids))
        .all()
        if employee_ids
        else []
    )
    linked_goals = [g for g in goals if g.linked_kpi_id is not None]
    progress_values = [
        min(100, round((g.current_value / g.target_value) * 100)) if g.target_value > 0 else 0
        for g in goals
    ]
    avg_goal_progress = round(sum(progress_values) / len(progress_values)) if progress_values else 0

    reviews = (
        db.query(KpiReview)
        .filter(KpiReview.review_period == review_period)
        .filter(KpiReview.employee_id.in_(employee_ids))
        .all()
        if employee_ids
        else []
    )
    avg_kpi_score = round(sum(r.total_score for r in reviews) / len(reviews)) if reviews else 0

    alignment_gap_count = 0
    for g in linked_goals:
        employee_review = next((r for r in reviews if r.employee_id == g.employee_id), None)
        if not employee_review:
            alignment_gap_count += 1
            continue
        goal_progress = min(100, round((g.current_value / g.target_value) * 100)) if g.target_value > 0 else 0
        if abs(goal_progress - employee_review.total_score) >= 20:
            alignment_gap_count += 1

    return GoalKpiCalibrationSummary(
        review_period=review_period,
        department_id=department_id,
        employee_goal_count=len(goals),
        linked_goal_count=len(linked_goals),
        avg_goal_progress_percent=avg_goal_progress,
        avg_kpi_score=avg_kpi_score,
        alignment_gap_count=alignment_gap_count,
    )
