from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    Department,
    Employee,
    KpiCalibrationItem,
    KpiCalibrationSession,
    KpiDefinition,
    KpiReview,
    KpiReviewItem,
    User,
)
from app.schemas.schemas import (
    BalancedScorecardSummary,
    KpiCalibrationSessionCreate,
    KpiCalibrationSessionRead,
    KpiDefinitionCreate,
    KpiDefinitionRead,
    KpiReviewCreate,
    KpiReviewItemRead,
    KpiReviewRead,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/kpi", tags=["Balanced Scorecard & KPI"])


def _label_from_score(total_score: int) -> str:
    if total_score >= 85:
        return "excellent"
    if total_score >= 70:
        return "good"
    if total_score >= 55:
        return "watchlist"
    return "critical"


@router.post("/definitions", response_model=KpiDefinitionRead)
def create_kpi_definition(
    payload: KpiDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "hr_manager")),
):
    item = KpiDefinition(**payload.model_dump(), created_by=current_user.username)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/definitions", response_model=list[KpiDefinitionRead])
def list_kpi_definitions(
    perspective: str | None = None,
    workforce_category: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(KpiDefinition)
    if perspective:
        query = query.filter(KpiDefinition.perspective == perspective)
    if workforce_category:
        query = query.filter(KpiDefinition.workforce_category == workforce_category)
    return query.order_by(KpiDefinition.created_at.desc()).all()


@router.post("/reviews", response_model=KpiReviewRead)
def create_kpi_review(
    payload: KpiReviewCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if payload.employee_id is None and payload.department_id is None:
        raise HTTPException(status_code=400, detail="employee_id or department_id is required")
    if payload.employee_id is not None and not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    if payload.department_id is not None and not db.query(Department).filter(Department.id == payload.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")
    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one KPI item is required")

    total_score = 0
    review = KpiReview(
        employee_id=payload.employee_id,
        department_id=payload.department_id,
        review_period=payload.review_period,
        total_score=0,
        performance_label="critical",
        notes=payload.notes,
        reviewed_by=payload.reviewed_by,
    )
    db.add(review)
    db.flush()

    for item in payload.items:
        kpi = db.query(KpiDefinition).filter(KpiDefinition.id == item.kpi_id).first()
        if not kpi:
            raise HTTPException(status_code=404, detail=f"KPI definition {item.kpi_id} not found")
        if kpi.target_value <= 0:
            achievement = 100
        elif kpi.is_higher_better:
            achievement = min(200, round((item.actual_value / kpi.target_value) * 100))
        else:
            achievement = min(200, round((kpi.target_value / max(1, item.actual_value)) * 100))
        weighted = round((achievement * kpi.weight_percent) / 100)
        total_score += weighted
        db.add(
            KpiReviewItem(
                review_id=review.id,
                kpi_id=kpi.id,
                actual_value=item.actual_value,
                achievement_percent=achievement,
                weighted_score=weighted,
            )
        )

    review.total_score = total_score
    review.performance_label = _label_from_score(total_score)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews", response_model=list[KpiReviewRead])
def list_kpi_reviews(
    review_period: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    query = db.query(KpiReview)
    if review_period:
        query = query.filter(KpiReview.review_period == review_period)
    return query.order_by(KpiReview.reviewed_at.desc()).all()


@router.get("/reviews/{review_id}/items", response_model=list[KpiReviewItemRead])
def list_kpi_review_items(
    review_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    review = db.query(KpiReview).filter(KpiReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="KPI review not found")
    return db.query(KpiReviewItem).filter(KpiReviewItem.review_id == review_id).all()


@router.get("/balanced-scorecard/summary", response_model=BalancedScorecardSummary)
def balanced_scorecard_summary(
    review_period: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    reviews_query = db.query(KpiReview)
    if review_period:
        reviews_query = reviews_query.filter(KpiReview.review_period == review_period)
    reviews = reviews_query.all()
    if not reviews:
        return BalancedScorecardSummary(
            review_count=0,
            avg_total_score=0,
            perspective_scores={},
            high_performer_count=0,
            low_performer_count=0,
        )

    avg_total = round(sum(r.total_score for r in reviews) / len(reviews))
    high_count = len([r for r in reviews if r.total_score >= 85])
    low_count = len([r for r in reviews if r.total_score < 55])

    perspective_totals: dict[str, list[int]] = {}
    for review in reviews:
        items = db.query(KpiReviewItem).filter(KpiReviewItem.review_id == review.id).all()
        for item in items:
            kpi = db.query(KpiDefinition).filter(KpiDefinition.id == item.kpi_id).first()
            if not kpi:
                continue
            perspective_totals.setdefault(kpi.perspective, []).append(item.weighted_score)
    perspective_scores = {
        key: round(sum(values) / len(values)) if values else 0
        for key, values in perspective_totals.items()
    }

    return BalancedScorecardSummary(
        review_count=len(reviews),
        avg_total_score=avg_total,
        perspective_scores=perspective_scores,
        high_performer_count=high_count,
        low_performer_count=low_count,
    )


@router.post("/calibration/sessions", response_model=KpiCalibrationSessionRead)
def create_kpi_calibration_session(
    payload: KpiCalibrationSessionCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Department).filter(Department.id == payload.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")
    if not payload.items:
        raise HTTPException(status_code=400, detail="Calibration items are required")

    session = KpiCalibrationSession(
        department_id=payload.department_id,
        review_period=payload.review_period,
        status="completed",
        created_by=payload.created_by,
        notes=payload.notes,
    )
    db.add(session)
    db.flush()

    for item in payload.items:
        review = db.query(KpiReview).filter(KpiReview.id == item.review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail=f"KPI review {item.review_id} not found")
        db.add(
            KpiCalibrationItem(
                session_id=session.id,
                review_id=review.id,
                original_score=review.total_score,
                calibrated_score=item.calibrated_score,
                rationale=item.rationale,
            )
        )
        review.total_score = item.calibrated_score
        review.performance_label = _label_from_score(item.calibrated_score)

    db.commit()
    db.refresh(session)
    return session


@router.get("/calibration/sessions", response_model=list[KpiCalibrationSessionRead])
def list_kpi_calibration_sessions(
    review_period: str | None = None,
    department_id: int | None = None,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    query = db.query(KpiCalibrationSession)
    if review_period is not None:
        query = query.filter(KpiCalibrationSession.review_period == review_period)
    if department_id is not None:
        query = query.filter(KpiCalibrationSession.department_id == department_id)
    return query.order_by(KpiCalibrationSession.created_at.desc()).all()
