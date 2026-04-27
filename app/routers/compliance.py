from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    ComplianceAlert,
    Employee,
    EmployeeComplianceCheck,
    RegulationRule,
    RegulationSource,
    RegulationUpdateLog,
    User,
)
from app.schemas.schemas import (
    ComplianceAlertRead,
    ComplianceDashboard,
    EmployeeComplianceCheckCreate,
    EmployeeComplianceCheckRead,
    EmployeeComplianceCheckReview,
    RegulationUpdateLogRead,
    RegulationRuleCreate,
    RegulationRuleRead,
    RegulationSourceCreate,
    RegulationSourceRead,
    SourceCheckResponse,
)
from app.services.compliance_monitor import check_source_website
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/compliance", tags=["Regulatory Compliance"])


@router.post("/sources", response_model=RegulationSourceRead)
def create_regulation_source(
    payload: RegulationSourceCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    existing = db.query(RegulationSource).filter(RegulationSource.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Regulation source already exists")
    item = RegulationSource(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/sources", response_model=list[RegulationSourceRead])
def list_regulation_sources(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(RegulationSource).filter(RegulationSource.is_active.is_(True)).all()


@router.post("/sources/{source_id}/check", response_model=SourceCheckResponse)
def check_regulation_source(
    source_id: int,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    source = db.query(RegulationSource).filter(RegulationSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Regulation source not found")

    result = check_source_website(source.website_url)
    previous_hash = source.last_content_hash
    change_detected = (
        result.status == "ok"
        and result.content_hash is not None
        and previous_hash is not None
        and result.content_hash != previous_hash
    )

    source.last_checked_at = datetime.utcnow()
    source.last_check_status = result.status
    source.last_error = None if result.status == "ok" else result.details
    if result.content_hash:
        source.last_content_hash = result.content_hash

    log = RegulationUpdateLog(
        source_id=source.id,
        status=result.status,
        change_detected=change_detected,
        content_hash=result.content_hash,
        page_title=result.page_title,
        details=result.details,
    )
    db.add(log)

    if change_detected:
        db.add(
            ComplianceAlert(
                source_id=source.id,
                alert_type="source_update_detected",
                title=f"Regulation update detected: {source.name}",
                message=(
                    "Website content fingerprint changed. "
                    "Compliance team should review latest regulations."
                ),
                severity="high",
            )
        )
    elif result.status != "ok":
        db.add(
            ComplianceAlert(
                source_id=source.id,
                alert_type="source_check_failed",
                title=f"Source check failed: {source.name}",
                message=f"Source monitoring failed with status {result.status}: {result.details}",
                severity="medium",
            )
        )

    db.commit()

    return SourceCheckResponse(
        source_id=source.id,
        source_name=source.name,
        status=result.status,
        change_detected=change_detected,
        details=result.details,
        checked_at=source.last_checked_at,
    )


@router.post("/sources/check-all", response_model=list[SourceCheckResponse])
def check_all_regulation_sources(
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    sources = db.query(RegulationSource).filter(RegulationSource.is_active.is_(True)).all()
    results: list[SourceCheckResponse] = []
    for source in sources:
        check_result = check_source_website(source.website_url)
        previous_hash = source.last_content_hash
        change_detected = (
            check_result.status == "ok"
            and check_result.content_hash is not None
            and previous_hash is not None
            and check_result.content_hash != previous_hash
        )

        source.last_checked_at = datetime.utcnow()
        source.last_check_status = check_result.status
        source.last_error = None if check_result.status == "ok" else check_result.details
        if check_result.content_hash:
            source.last_content_hash = check_result.content_hash

        db.add(
            RegulationUpdateLog(
                source_id=source.id,
                status=check_result.status,
                change_detected=change_detected,
                content_hash=check_result.content_hash,
                page_title=check_result.page_title,
                details=check_result.details,
            )
        )
        if change_detected:
            db.add(
                ComplianceAlert(
                    source_id=source.id,
                    alert_type="source_update_detected",
                    title=f"Regulation update detected: {source.name}",
                    message="Website content changed. Verify new regulations immediately.",
                    severity="high",
                )
            )
        elif check_result.status != "ok":
            db.add(
                ComplianceAlert(
                    source_id=source.id,
                    alert_type="source_check_failed",
                    title=f"Source check failed: {source.name}",
                    message=(
                        f"Could not check source website. "
                        f"Status: {check_result.status}, details: {check_result.details}"
                    ),
                    severity="medium",
                )
            )
        results.append(
            SourceCheckResponse(
                source_id=source.id,
                source_name=source.name,
                status=check_result.status,
                change_detected=change_detected,
                details=check_result.details,
                checked_at=source.last_checked_at,
            )
        )
    db.commit()
    return results


@router.post("/rules", response_model=RegulationRuleRead)
def create_regulation_rule(
    payload: RegulationRuleCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(RegulationSource).filter(RegulationSource.id == payload.source_id).first():
        raise HTTPException(status_code=404, detail="Regulation source not found")
    rule = RegulationRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/rules", response_model=list[RegulationRuleRead])
def list_regulation_rules(
    worker_category: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(RegulationRule).filter(RegulationRule.status == "active")
    if worker_category:
        query = query.filter(RegulationRule.worker_category == worker_category)
    return query.order_by(RegulationRule.updated_at.desc()).all()


@router.post("/checks", response_model=EmployeeComplianceCheckRead)
def create_employee_compliance_check(
    payload: EmployeeComplianceCheckCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    if not db.query(RegulationRule).filter(RegulationRule.id == payload.regulation_id).first():
        raise HTTPException(status_code=404, detail="Regulation rule not found")
    check = EmployeeComplianceCheck(**payload.model_dump())
    db.add(check)
    db.commit()
    db.refresh(check)
    return check


@router.patch("/checks/{check_id}/review", response_model=EmployeeComplianceCheckRead)
def review_employee_compliance_check(
    check_id: int,
    payload: EmployeeComplianceCheckReview,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    check = db.query(EmployeeComplianceCheck).filter(EmployeeComplianceCheck.id == check_id).first()
    if not check:
        raise HTTPException(status_code=404, detail="Compliance check not found")
    check.verification_status = payload.verification_status
    check.verified_by = payload.verified_by
    check.verified_at = datetime.utcnow()
    check.notes = payload.notes
    db.commit()
    db.refresh(check)
    return check


@router.get("/checks", response_model=list[EmployeeComplianceCheckRead])
def list_employee_compliance_checks(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(EmployeeComplianceCheck).order_by(EmployeeComplianceCheck.id.desc()).all()


@router.get("/logs", response_model=list[RegulationUpdateLogRead])
def list_regulation_update_logs(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(RegulationUpdateLog).order_by(RegulationUpdateLog.check_time.desc()).limit(100).all()


@router.get("/alerts", response_model=list[ComplianceAlertRead])
def list_compliance_alerts(
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(ComplianceAlert)
    if unresolved_only:
        query = query.filter(ComplianceAlert.is_resolved.is_(False))
    return query.order_by(ComplianceAlert.created_at.desc()).limit(100).all()


@router.get("/dashboard", response_model=ComplianceDashboard)
def compliance_dashboard(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    expiring_threshold = datetime.utcnow().date() + timedelta(days=30)
    total_sources = db.query(func.count(RegulationSource.id)).scalar() or 0
    sources_with_errors = (
        db.query(func.count(RegulationSource.id))
        .filter(RegulationSource.last_check_status.isnot(None))
        .filter(RegulationSource.last_check_status != "ok")
        .scalar()
        or 0
    )
    total_rules = db.query(func.count(RegulationRule.id)).scalar() or 0
    rules_tenaga_kesehatan = (
        db.query(func.count(RegulationRule.id))
        .filter(RegulationRule.worker_category == "tenaga_kesehatan")
        .scalar()
        or 0
    )
    rules_non_kesehatan = (
        db.query(func.count(RegulationRule.id))
        .filter(RegulationRule.worker_category == "non_kesehatan")
        .scalar()
        or 0
    )
    total_checks = db.query(func.count(EmployeeComplianceCheck.id)).scalar() or 0
    pending_checks = (
        db.query(func.count(EmployeeComplianceCheck.id))
        .filter(EmployeeComplianceCheck.verification_status == "pending")
        .scalar()
        or 0
    )
    expiring_30_days = (
        db.query(func.count(EmployeeComplianceCheck.id))
        .filter(EmployeeComplianceCheck.expiry_date.isnot(None))
        .filter(EmployeeComplianceCheck.expiry_date <= expiring_threshold)
        .scalar()
        or 0
    )
    unresolved_alerts = (
        db.query(func.count(ComplianceAlert.id))
        .filter(ComplianceAlert.is_resolved.is_(False))
        .scalar()
        or 0
    )
    return ComplianceDashboard(
        total_sources=total_sources,
        sources_with_errors=sources_with_errors,
        total_rules=total_rules,
        rules_tenaga_kesehatan=rules_tenaga_kesehatan,
        rules_non_kesehatan=rules_non_kesehatan,
        total_checks=total_checks,
        pending_checks=pending_checks,
        expiring_30_days=expiring_30_days,
        unresolved_alerts=unresolved_alerts,
    )
