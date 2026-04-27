from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="staff")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    job_title: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active")

    department: Mapped["Department"] = relationship(back_populates="employees")
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(back_populates="employee")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee: Mapped["Employee"] = relationship(back_populates="leave_requests")


class RegulationSource(Base):
    __tablename__ = "regulation_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    institution_level: Mapped[str] = mapped_column(String(50), nullable=False)
    website_url: Mapped[str] = mapped_column(String(255), nullable=False)
    region_scope: Mapped[str] = mapped_column(String(100), default="Bali")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_check_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    regulations: Mapped[list["RegulationRule"]] = relationship(back_populates="source")
    update_logs: Mapped[list["RegulationUpdateLog"]] = relationship(back_populates="source")


class RegulationRule(Base):
    __tablename__ = "regulation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("regulation_sources.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    regulation_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    worker_category: Mapped[str] = mapped_column(String(30), nullable=False, default="non_kesehatan")
    requirement_type: Mapped[str] = mapped_column(String(60), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    reference_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["RegulationSource"] = relationship(back_populates="regulations")
    employee_checks: Mapped[list["EmployeeComplianceCheck"]] = relationship(back_populates="regulation")


class EmployeeComplianceCheck(Base):
    __tablename__ = "employee_compliance_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    regulation_id: Mapped[int] = mapped_column(ForeignKey("regulation_rules.id"), nullable=False)
    required_document: Mapped[str] = mapped_column(String(150), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending")
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped["Employee"] = relationship()
    regulation: Mapped["RegulationRule"] = relationship(back_populates="employee_checks")


class RegulationUpdateLog(Base):
    __tablename__ = "regulation_update_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("regulation_sources.id"), nullable=False)
    check_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    change_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    page_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped["RegulationSource"] = relationship(back_populates="update_logs")


class ComplianceAlert(Base):
    __tablename__ = "compliance_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("regulation_sources.id"), nullable=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["RegulationSource"] = relationship()


class TrainingNeedAnalysis(Base):
    __tablename__ = "training_need_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    workforce_category: Mapped[str] = mapped_column(String(30), nullable=False)
    role_name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    target_count: Mapped[int] = mapped_column(Integer, default=1)
    competency_gap: Mapped[str] = mapped_column(Text, nullable=False)
    mandatory_regulation_ref: Mapped[str | None] = mapped_column(String(150), nullable=True)
    recommended_training: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    verified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department: Mapped["Department"] = relationship()


class WorkloadAnalysis(Base):
    __tablename__ = "workload_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_name: Mapped[str] = mapped_column(String(255), nullable=False)
    workforce_category: Mapped[str] = mapped_column(String(30), nullable=False)
    service_type: Mapped[str] = mapped_column(String(30), nullable=False, default="rawat_inap")
    unit_type: Mapped[str] = mapped_column(String(40), nullable=False, default="general_ward")
    model_type: Mapped[str] = mapped_column(String(30), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    service_volume: Mapped[int] = mapped_column(Integer, nullable=False)
    total_workload_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    available_working_hours_per_staff: Mapped[int] = mapped_column(Integer, nullable=False)
    allowance_factor: Mapped[int] = mapped_column(Integer, default=100)  # stored as percent
    min_regulatory_staffing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_staff_count: Mapped[int] = mapped_column(Integer, nullable=False)
    optimum_staff_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_staff_count: Mapped[int] = mapped_column(Integer, nullable=False)
    staffing_gap: Mapped[int] = mapped_column(Integer, nullable=False)
    overcapacity_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ebitda_margin_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cashflow_coverage_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    financial_pressure_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    regulation_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    regulations_last_sync_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department: Mapped["Department"] = relationship()


class WorkloadRefreshSchedule(Base):
    __tablename__ = "workload_refresh_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("workload_analyses.id"), nullable=False, unique=True)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis: Mapped["WorkloadAnalysis"] = relationship()


class KpiDefinition(Base):
    __tablename__ = "kpi_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    perspective: Mapped[str] = mapped_column(String(30), nullable=False)
    workforce_category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False, default="score")
    weight_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    is_higher_better: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class KpiReview(Base):
    __tablename__ = "kpi_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    review_period: Mapped[str] = mapped_column(String(50), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    performance_label: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee: Mapped["Employee"] = relationship()
    department: Mapped["Department"] = relationship()


class KpiReviewItem(Base):
    __tablename__ = "kpi_review_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("kpi_reviews.id"), nullable=False)
    kpi_id: Mapped[int] = mapped_column(ForeignKey("kpi_definitions.id"), nullable=False)
    actual_value: Mapped[int] = mapped_column(Integer, nullable=False)
    achievement_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    weighted_score: Mapped[int] = mapped_column(Integer, nullable=False)

    review: Mapped["KpiReview"] = relationship()
    kpi: Mapped["KpiDefinition"] = relationship()


class PayrollProfile(Base):
    __tablename__ = "payroll_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), unique=True, nullable=False)
    base_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_status: Mapped[str] = mapped_column(String(20), nullable=False, default="TK0")
    bpjs_kesehatan_enrolled: Mapped[bool] = mapped_column(Boolean, default=True)
    bpjs_ketenagakerjaan_enrolled: Mapped[bool] = mapped_column(Boolean, default=True)
    npwp_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee: Mapped["Employee"] = relationship()


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    run_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(20), default="processed")
    processed_by: Mapped[str] = mapped_column(String(100), nullable=False)


class PayrollItem(Base):
    __tablename__ = "payroll_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payroll_run_id: Mapped[int] = mapped_column(ForeignKey("payroll_runs.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    gross_salary: Mapped[int] = mapped_column(Integer, nullable=False)
    overtime_pay: Mapped[int] = mapped_column(Integer, default=0)
    allowance_total: Mapped[int] = mapped_column(Integer, default=0)
    deduction_total: Mapped[int] = mapped_column(Integer, default=0)
    pph21_tax: Mapped[int] = mapped_column(Integer, default=0)
    bpjs_total: Mapped[int] = mapped_column(Integer, default=0)
    net_salary: Mapped[int] = mapped_column(Integer, nullable=False)

    payroll_run: Mapped["PayrollRun"] = relationship()
    employee: Mapped["Employee"] = relationship()


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    check_out_time: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="present")
    source: Mapped[str] = mapped_column(String(20), default="manual")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped["Employee"] = relationship()


class ShiftSchedule(Base):
    __tablename__ = "shift_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_type: Mapped[str] = mapped_column(String(20), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    unit_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    employee: Mapped["Employee"] = relationship()


class OvertimeRecord(Base):
    __tablename__ = "overtime_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    overtime_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)

    employee: Mapped["Employee"] = relationship()


class RecruitmentPosition(Base):
    __tablename__ = "recruitment_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    workforce_category: Mapped[str] = mapped_column(String(30), nullable=False)
    open_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    department: Mapped["Department"] = relationship()


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("recruitment_positions.id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    stage: Mapped[str] = mapped_column(String(30), default="screening")
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    position: Mapped["RecruitmentPosition"] = relationship()


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    task_name: Mapped[str] = mapped_column(String(150), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    employee: Mapped["Employee"] = relationship()


class EmployeeGoal(Base):
    __tablename__ = "employee_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_period: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, default=0)
    linked_kpi_id: Mapped[int | None] = mapped_column(ForeignKey("kpi_definitions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="on_track")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee: Mapped["Employee"] = relationship()
    linked_kpi: Mapped["KpiDefinition"] = relationship()


class KpiCalibrationSession(Base):
    __tablename__ = "kpi_calibration_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    review_period: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department: Mapped["Department"] = relationship()


class KpiCalibrationItem(Base):
    __tablename__ = "kpi_calibration_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("kpi_calibration_sessions.id"), nullable=False)
    review_id: Mapped[int] = mapped_column(ForeignKey("kpi_reviews.id"), nullable=False)
    original_score: Mapped[int] = mapped_column(Integer, nullable=False)
    calibrated_score: Mapped[int] = mapped_column(Integer, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["KpiCalibrationSession"] = relationship()
    review: Mapped["KpiReview"] = relationship()
