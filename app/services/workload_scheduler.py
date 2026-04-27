from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.models import ComplianceAlert, WorkloadAnalysis, WorkloadRefreshSchedule
from app.services.workload_engine import (
    calculate_financial_pressure_index,
    calculate_optimum_staff_count,
    calculate_recommended_staff,
)


def _interval_days(frequency: str) -> int:
    return 7 if frequency == "weekly" else 30


def run_due_workload_schedules(db: Session) -> dict:
    now = datetime.utcnow()
    due_items = (
        db.query(WorkloadRefreshSchedule)
        .filter(WorkloadRefreshSchedule.enabled.is_(True))
        .filter(WorkloadRefreshSchedule.next_run_at <= now)
        .all()
    )
    processed = 0
    succeeded = 0
    failed = 0
    summaries: list[str] = []

    for schedule in due_items:
        processed += 1
        analysis = db.query(WorkloadAnalysis).filter(WorkloadAnalysis.id == schedule.analysis_id).first()
        if not analysis:
            schedule.last_status = "failed"
            schedule.last_summary = "Analysis not found"
            schedule.last_run_at = now
            schedule.next_run_at = now + timedelta(days=_interval_days(schedule.frequency))
            failed += 1
            continue

        try:
            recommended = calculate_recommended_staff(
                model_type=analysis.model_type,
                workforce_category=analysis.workforce_category,
                service_type=analysis.service_type,
                unit_type=analysis.unit_type,
                service_volume=analysis.service_volume,
                total_workload_hours=analysis.total_workload_hours,
                available_working_hours_per_staff=analysis.available_working_hours_per_staff,
                allowance_factor_percent=analysis.allowance_factor,
            )
            if analysis.min_regulatory_staffing is not None:
                recommended = max(recommended, analysis.min_regulatory_staffing)
            financial_pressure_index = calculate_financial_pressure_index(
                analysis.ebitda_margin_percent,
                analysis.cashflow_coverage_months,
            )
            optimum = calculate_optimum_staff_count(
                recommended_staff_count=recommended,
                min_regulatory_staffing=analysis.min_regulatory_staffing,
                financial_pressure_index=financial_pressure_index,
            )

            analysis.recommended_staff_count = recommended
            analysis.optimum_staff_count = optimum
            analysis.staffing_gap = optimum - analysis.current_staff_count
            analysis.overcapacity_count = max(0, analysis.current_staff_count - optimum)
            analysis.financial_pressure_index = financial_pressure_index
            analysis.regulations_last_sync_at = now
            analysis.next_review_at = now + timedelta(days=_interval_days(schedule.frequency))

            schedule.last_status = "success"
            schedule.last_run_at = now
            schedule.next_run_at = now + timedelta(days=_interval_days(schedule.frequency))
            schedule.last_summary = (
                f"{analysis.analysis_name}: recommended {recommended}, "
                f"optimum {optimum}, current {analysis.current_staff_count}, gap {analysis.staffing_gap}"
            )
            succeeded += 1
            summaries.append(schedule.last_summary)

            if analysis.staffing_gap > 0:
                db.add(
                    ComplianceAlert(
                        source_id=None,
                        alert_type="workload_gap_detected",
                        title=f"Workload gap detected - {analysis.analysis_name}",
                        message=(
                            f"Service {analysis.service_type}/{analysis.unit_type} requires "
                            f"{recommended} staff; current is {analysis.current_staff_count}. "
                            f"Gap: {analysis.staffing_gap}."
                        ),
                        severity="high" if analysis.staffing_gap >= 3 else "medium",
                    )
                )
        except Exception as exc:  # pragma: no cover
            schedule.last_status = "failed"
            schedule.last_summary = str(exc)
            schedule.last_run_at = now
            schedule.next_run_at = now + timedelta(days=_interval_days(schedule.frequency))
            failed += 1

    db.commit()
    return {
        "processed": processed,
        "succeeded": succeeded,
        "failed": failed,
        "summaries": summaries,
    }
