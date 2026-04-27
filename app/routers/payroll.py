from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Employee, OvertimeRecord, PayrollItem, PayrollProfile, PayrollRun, User
from app.schemas.schemas import (
    PayrollItemRead,
    PayrollProfileCreate,
    PayrollProfileRead,
    PayrollRunCreate,
    PayrollRunRead,
)
from app.services.auth import get_current_user, require_roles

router = APIRouter(prefix="/payroll", tags=["Payroll & Taxes"])


def _estimate_pph21(gross_salary: int, tax_status: str) -> int:
    bracket_rate = 0.05 if gross_salary <= 10_000_000 else 0.1
    non_taxable_adjustment = 500_000 if tax_status.startswith("K") else 0
    taxable_income = max(0, gross_salary - non_taxable_adjustment)
    return round(taxable_income * bracket_rate)


@router.post("/profiles", response_model=PayrollProfileRead)
def upsert_payroll_profile(
    payload: PayrollProfileCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    if not db.query(Employee).filter(Employee.id == payload.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")
    profile = db.query(PayrollProfile).filter(PayrollProfile.employee_id == payload.employee_id).first()
    if profile:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    else:
        profile = PayrollProfile(**payload.model_dump())
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profiles", response_model=list[PayrollProfileRead])
def list_payroll_profiles(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return db.query(PayrollProfile).all()


@router.post("/run", response_model=PayrollRunRead)
def create_payroll_run(
    payload: PayrollRunCreate,
    db: Session = Depends(get_db),
    _manager: User = Depends(require_roles("admin", "hr_manager")),
):
    payroll_run = PayrollRun(**payload.model_dump(), status="processed")
    db.add(payroll_run)
    db.flush()

    profiles = db.query(PayrollProfile).all()
    for profile in profiles:
        approved_overtime_hours = (
            db.query(OvertimeRecord)
            .filter(OvertimeRecord.employee_id == profile.employee_id)
            .filter(OvertimeRecord.status == "approved")
            .all()
        )
        overtime_total = sum(x.hours for x in approved_overtime_hours)
        overtime_pay = overtime_total * 50_000
        gross_salary = profile.base_salary + overtime_pay
        bpjs_total = round(gross_salary * 0.03) if (
            profile.bpjs_kesehatan_enrolled or profile.bpjs_ketenagakerjaan_enrolled
        ) else 0
        pph21 = _estimate_pph21(gross_salary, profile.tax_status)
        net_salary = gross_salary - pph21 - bpjs_total

        db.add(
            PayrollItem(
                payroll_run_id=payroll_run.id,
                employee_id=profile.employee_id,
                gross_salary=gross_salary,
                overtime_pay=overtime_pay,
                allowance_total=0,
                deduction_total=0,
                pph21_tax=pph21,
                bpjs_total=bpjs_total,
                net_salary=net_salary,
            )
        )

    db.commit()
    db.refresh(payroll_run)
    return payroll_run


@router.get("/run/{run_id}/items", response_model=list[PayrollItemRead])
def list_payroll_items(
    run_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    run = db.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Payroll run not found")
    return db.query(PayrollItem).filter(PayrollItem.payroll_run_id == run_id).all()
