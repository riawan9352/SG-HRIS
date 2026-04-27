from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Department, WorkloadAnalysis, WorkloadRefreshSchedule, User
from app.schemas.schemas import (
    WorkloadAnalysisCreate,
    WorkloadAnalysisRead,
    WorkloadRefreshRequest,
    WorkloadScheduleCreate,
    WorkloadScheduleRead,
    WorkloadSchedulerRunResponse,
    WorkloadScheduleUpdate,
)
from app.services.auth import get_current_user, require_roles
from app.services.workload_engine import (
    calculate_financial_pressure_index,
    calculate_optimum_staff_count,
    calculate_recommended_staff,
)
from app.services.workload_scheduler import run_due_workload_schedules

router = APIRouter(prefix="/workload-analysis", tags=["Workload Analysis"])


@router.post("/", response_model=WorkloadAnalysisRead)
def create_workload_analysis(
    payload: WorkloadAnalysisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "hr_manager")),
):
    if payload.department_id is not None:
        department = db.query(Department).filter(Department.id == payload.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end must be after period_start")

    try:
        recommended = calculate_recommended_staff(
            model_type=payload.model_type,
            workforce_category=payload.workforce_category,
            service_type=payload.service_type,
            unit_type=payload.unit_type,
            service_volume=payload.service_volume,
            total_workload_hours=payload.total_workload_hours,
            available_working_hours_per_staff=payload.available_working_hours_per_staff,
            allowance_factor_percent=payload.allowance_factor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if payload.min_regulatory_staffing is not None:
        recommended = max(recommended, payload.min_regulatory_staffing)
    financial_pressure_index = calculate_financial_pressure_index(
        payload.ebitda_margin_percent,
        payload.cashflow_coverage_months,
    )
    optimum = calculate_optimum_staff_count(
        recommended_staff_count=recommended,
        min_regulatory_staffing=payload.min_regulatory_staffing,
        financial_pressure_index=financial_pressure_index,
    )

    item = WorkloadAnalysis(
        **payload.model_dump(),
        recommended_staff_count=recommended,
        optimum_staff_count=optimum,
        staffing_gap=optimum - payload.current_staff_count,
        overcapacity_count=max(0, payload.current_staff_count - optimum),
        financial_pressure_index=financial_pressure_index,
        regulations_last_sync_at=datetime.utcnow(),
        next_review_at=datetime.utcnow() + timedelta(days=30),
        created_by=current_user.username,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=list[WorkloadAnalysisRead])
def list_workload_analyses(
    workforce_category: str | None = None,
    model_type: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(WorkloadAnalysis)
    if workforce_category:
        query = query.filter(WorkloadAnalysis.workforce_category == workforce_category)
    if model_type:
        query = query.filter(WorkloadAnalysis.model_type == model_type)
    return query.order_by(WorkloadAnalysis.created_at.desc()).all()


@router.post("/{analysis_id}/refresh", response_model=WorkloadAnalysisRead)
def refresh_workload_analysis(
    analysis_id: int,
    payload: WorkloadRefreshRequest,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    item = db.query(WorkloadAnalysis).filter(WorkloadAnalysis.id == analysis_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Workload analysis not found")

    recommended = calculate_recommended_staff(
        model_type=item.model_type,
        workforce_category=item.workforce_category,
        service_type=item.service_type,
        unit_type=item.unit_type,
        service_volume=item.service_volume,
        total_workload_hours=item.total_workload_hours,
        available_working_hours_per_staff=item.available_working_hours_per_staff,
        allowance_factor_percent=item.allowance_factor,
    )
    if item.min_regulatory_staffing is not None:
        recommended = max(recommended, item.min_regulatory_staffing)
    if payload.ebitda_margin_percent is not None:
        item.ebitda_margin_percent = payload.ebitda_margin_percent
    if payload.cashflow_coverage_months is not None:
        item.cashflow_coverage_months = payload.cashflow_coverage_months
    financial_pressure_index = calculate_financial_pressure_index(
        item.ebitda_margin_percent,
        item.cashflow_coverage_months,
    )
    optimum = calculate_optimum_staff_count(
        recommended_staff_count=recommended,
        min_regulatory_staffing=item.min_regulatory_staffing,
        financial_pressure_index=financial_pressure_index,
    )

    item.recommended_staff_count = recommended
    item.optimum_staff_count = optimum
    item.staffing_gap = optimum - item.current_staff_count
    item.overcapacity_count = max(0, item.current_staff_count - optimum)
    item.financial_pressure_index = financial_pressure_index
    item.regulations_last_sync_at = datetime.utcnow()
    item.next_review_at = datetime.utcnow() + timedelta(days=payload.review_interval_days)
    if payload.regulation_context is not None:
        item.regulation_context = payload.regulation_context

    db.commit()
    db.refresh(item)
    return item


@router.post("/{analysis_id}/schedule", response_model=WorkloadScheduleRead)
def create_workload_schedule(
    analysis_id: int,
    payload: WorkloadScheduleCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    analysis = db.query(WorkloadAnalysis).filter(WorkloadAnalysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Workload analysis not found")
    existing = db.query(WorkloadRefreshSchedule).filter(WorkloadRefreshSchedule.analysis_id == analysis_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Schedule already exists for this analysis")
    schedule = WorkloadRefreshSchedule(
        analysis_id=analysis_id,
        frequency=payload.frequency,
        enabled=True,
        next_run_at=datetime.utcnow() + timedelta(days=payload.start_in_days),
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.patch("/{analysis_id}/schedule", response_model=WorkloadScheduleRead)
def update_workload_schedule(
    analysis_id: int,
    payload: WorkloadScheduleUpdate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    schedule = db.query(WorkloadRefreshSchedule).filter(WorkloadRefreshSchedule.analysis_id == analysis_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found for this analysis")
    updates = payload.model_dump(exclude_unset=True)
    if "frequency" in updates:
        schedule.frequency = updates["frequency"]
    if "enabled" in updates:
        schedule.enabled = updates["enabled"]
    if "next_run_in_days" in updates:
        schedule.next_run_at = datetime.utcnow() + timedelta(days=updates["next_run_in_days"])
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/schedules", response_model=list[WorkloadScheduleRead])
def list_workload_schedules(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(WorkloadRefreshSchedule).order_by(WorkloadRefreshSchedule.next_run_at.asc()).all()


@router.post("/scheduler/run-due", response_model=WorkloadSchedulerRunResponse)
def run_due_scheduler_jobs(
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    return WorkloadSchedulerRunResponse(**run_due_workload_schedules(db))
