from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "staff"


class UserRead(BaseModel):
    id: int
    username: str
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: str | None = None


class DepartmentRead(DepartmentCreate):
    id: int

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    gender: str | None = None
    job_title: str
    phone: str | None = None
    email: EmailStr
    hire_date: date
    department_id: int
    status: str = "active"


class EmployeeRead(EmployeeCreate):
    id: int

    class Config:
        from_attributes = True


class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveApproval(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    approved_by: str


class LeaveRequestRead(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None
    status: str
    approved_by: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RegulationSourceCreate(BaseModel):
    name: str
    institution_level: str = Field(
        pattern="^(pemerintah_pusat|kemenaker|kemenkes|pemerintah_daerah|dinas_terkait)$"
    )
    website_url: str
    region_scope: str = "Bali"


class RegulationSourceRead(RegulationSourceCreate):
    id: int
    is_active: bool
    last_checked_at: datetime | None
    last_check_status: str | None
    last_error: str | None

    class Config:
        from_attributes = True


class RegulationRuleCreate(BaseModel):
    source_id: int
    title: str
    regulation_code: str | None = None
    worker_category: str = Field(pattern="^(tenaga_kesehatan|non_kesehatan)$")
    requirement_type: str
    summary: str
    effective_date: date | None = None
    review_due_date: date | None = None
    reference_url: str | None = None


class RegulationRuleRead(RegulationRuleCreate):
    id: int
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class EmployeeComplianceCheckCreate(BaseModel):
    employee_id: int
    regulation_id: int
    required_document: str
    document_number: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None


class EmployeeComplianceCheckReview(BaseModel):
    verification_status: str = Field(pattern="^(pending|verified|expired|rejected)$")
    verified_by: str
    notes: str | None = None


class EmployeeComplianceCheckRead(BaseModel):
    id: int
    employee_id: int
    regulation_id: int
    required_document: str
    document_number: str | None
    issued_date: date | None
    expiry_date: date | None
    verification_status: str
    verified_by: str | None
    verified_at: datetime | None
    notes: str | None

    class Config:
        from_attributes = True


class SourceCheckResponse(BaseModel):
    source_id: int
    source_name: str
    status: str
    change_detected: bool
    details: str
    checked_at: datetime


class RegulationUpdateLogRead(BaseModel):
    id: int
    source_id: int
    check_time: datetime
    status: str
    change_detected: bool
    page_title: str | None
    details: str | None

    class Config:
        from_attributes = True


class ComplianceAlertRead(BaseModel):
    id: int
    source_id: int | None
    alert_type: str
    title: str
    message: str
    severity: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplianceDashboard(BaseModel):
    total_sources: int
    sources_with_errors: int
    total_rules: int
    rules_tenaga_kesehatan: int
    rules_non_kesehatan: int
    total_checks: int
    pending_checks: int
    expiring_30_days: int
    unresolved_alerts: int


class TrainingNeedAnalysisCreate(BaseModel):
    title: str
    workforce_category: str = Field(pattern="^(nurse|medic|non_medic|support|other)$")
    role_name: str
    department_id: int | None = None
    target_count: int = Field(ge=1)
    competency_gap: str
    mandatory_regulation_ref: str | None = None
    recommended_training: str
    priority: str = Field(pattern="^(low|medium|high|critical)$")


class TrainingNeedAnalysisUpdate(BaseModel):
    title: str | None = None
    role_name: str | None = None
    department_id: int | None = None
    target_count: int | None = Field(default=None, ge=1)
    competency_gap: str | None = None
    mandatory_regulation_ref: str | None = None
    recommended_training: str | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
    status: str | None = Field(default=None, pattern="^(draft|proposed|approved|rejected)$")


class TrainingNeedAnalysisVerify(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    verified_by: str
    verification_notes: str | None = None


class TrainingNeedAnalysisRead(BaseModel):
    id: int
    title: str
    workforce_category: str
    role_name: str
    department_id: int | None
    target_count: int
    competency_gap: str
    mandatory_regulation_ref: str | None
    recommended_training: str
    priority: str
    status: str
    created_by: str
    verified_by: str | None
    verified_at: datetime | None
    verification_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkloadAnalysisCreate(BaseModel):
    analysis_name: str
    workforce_category: str = Field(pattern="^(nurse|medic|non_medic|support|other)$")
    service_type: str = Field(
        pattern="^(igd|icu|ok|rawat_inap|rawat_jalan|farmasi|penunjang|administrasi|other)$"
    )
    unit_type: str
    model_type: str = Field(pattern="^(hours_based|ratio_based|wisn_simplified)$")
    period_start: date
    period_end: date
    department_id: int | None = None
    service_volume: int = Field(ge=0)
    total_workload_hours: int = Field(ge=0)
    available_working_hours_per_staff: int = Field(gt=0)
    allowance_factor: int = Field(default=100, ge=50, le=300)
    min_regulatory_staffing: int | None = Field(default=None, ge=0)
    current_staff_count: int = Field(ge=0)
    revenue_amount: int | None = Field(default=None, ge=0)
    ebitda_margin_percent: int | None = Field(default=None, ge=-100, le=100)
    cashflow_coverage_months: int | None = Field(default=None, ge=0, le=60)
    regulation_context: str | None = None


class WorkloadAnalysisRead(BaseModel):
    id: int
    analysis_name: str
    workforce_category: str
    service_type: str
    unit_type: str
    model_type: str
    period_start: date
    period_end: date
    department_id: int | None
    service_volume: int
    total_workload_hours: int
    available_working_hours_per_staff: int
    allowance_factor: int
    min_regulatory_staffing: int | None
    recommended_staff_count: int
    optimum_staff_count: int
    current_staff_count: int
    staffing_gap: int
    overcapacity_count: int
    revenue_amount: int | None
    ebitda_margin_percent: int | None
    cashflow_coverage_months: int | None
    financial_pressure_index: int | None
    regulation_context: str | None
    regulations_last_sync_at: datetime | None
    next_review_at: datetime | None
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class WorkloadRefreshRequest(BaseModel):
    review_interval_days: int = Field(default=30, ge=1, le=365)
    regulation_context: str | None = None
    ebitda_margin_percent: int | None = Field(default=None, ge=-100, le=100)
    cashflow_coverage_months: int | None = Field(default=None, ge=0, le=60)


class WorkloadScheduleCreate(BaseModel):
    frequency: str = Field(pattern="^(weekly|monthly)$")
    start_in_days: int = Field(default=1, ge=0, le=60)


class WorkloadScheduleRead(BaseModel):
    id: int
    analysis_id: int
    frequency: str
    enabled: bool
    next_run_at: datetime
    last_run_at: datetime | None
    last_status: str | None
    last_summary: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkloadScheduleUpdate(BaseModel):
    frequency: str | None = Field(default=None, pattern="^(weekly|monthly)$")
    enabled: bool | None = None
    next_run_in_days: int | None = Field(default=None, ge=0, le=60)


class WorkloadSchedulerRunResponse(BaseModel):
    processed: int
    succeeded: int
    failed: int
    summaries: list[str]


class KpiDefinitionCreate(BaseModel):
    name: str
    perspective: str = Field(pattern="^(financial|customer|internal_process|learning_growth)$")
    workforce_category: str | None = Field(default=None, pattern="^(nurse|medic|non_medic|support|other)$")
    service_type: str | None = Field(
        default=None,
        pattern="^(igd|icu|ok|rawat_inap|rawat_jalan|farmasi|penunjang|administrasi|other)$",
    )
    target_value: int = Field(ge=0)
    unit: str = "score"
    weight_percent: int = Field(default=25, ge=1, le=100)
    is_higher_better: bool = True
    description: str | None = None


class KpiDefinitionRead(BaseModel):
    id: int
    name: str
    perspective: str
    workforce_category: str | None
    service_type: str | None
    target_value: int
    unit: str
    weight_percent: int
    is_higher_better: bool
    description: str | None
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class KpiReviewItemInput(BaseModel):
    kpi_id: int
    actual_value: int = Field(ge=0)


class KpiReviewCreate(BaseModel):
    employee_id: int | None = None
    department_id: int | None = None
    review_period: str
    reviewed_by: str
    notes: str | None = None
    items: list[KpiReviewItemInput]


class KpiReviewItemRead(BaseModel):
    id: int
    review_id: int
    kpi_id: int
    actual_value: int
    achievement_percent: int
    weighted_score: int

    class Config:
        from_attributes = True


class KpiReviewRead(BaseModel):
    id: int
    employee_id: int | None
    department_id: int | None
    review_period: str
    total_score: int
    performance_label: str
    notes: str | None
    reviewed_by: str
    reviewed_at: datetime

    class Config:
        from_attributes = True


class BalancedScorecardSummary(BaseModel):
    review_count: int
    avg_total_score: int
    perspective_scores: dict[str, int]
    high_performer_count: int
    low_performer_count: int


class PayrollProfileCreate(BaseModel):
    employee_id: int
    base_salary: int = Field(gt=0)
    tax_status: str = "TK0"
    bpjs_kesehatan_enrolled: bool = True
    bpjs_ketenagakerjaan_enrolled: bool = True
    npwp_number: str | None = None
    bank_account: str | None = None


class PayrollProfileRead(BaseModel):
    id: int
    employee_id: int
    base_salary: int
    tax_status: str
    bpjs_kesehatan_enrolled: bool
    bpjs_ketenagakerjaan_enrolled: bool
    npwp_number: str | None
    bank_account: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


class PayrollRunCreate(BaseModel):
    period_month: int = Field(ge=1, le=12)
    period_year: int = Field(ge=2020, le=2100)
    processed_by: str


class PayrollRunRead(BaseModel):
    id: int
    period_month: int
    period_year: int
    run_date: datetime
    status: str
    processed_by: str

    class Config:
        from_attributes = True


class PayrollItemRead(BaseModel):
    id: int
    payroll_run_id: int
    employee_id: int
    gross_salary: int
    overtime_pay: int
    allowance_total: int
    deduction_total: int
    pph21_tax: int
    bpjs_total: int
    net_salary: int

    class Config:
        from_attributes = True


class AttendanceCreate(BaseModel):
    employee_id: int
    attendance_date: date
    check_in_time: str | None = None
    check_out_time: str | None = None
    status: str = Field(pattern="^(present|absent|leave|sick)$")
    source: str = Field(pattern="^(manual|mobile|biometric)$", default="manual")
    notes: str | None = None


class AttendanceRead(AttendanceCreate):
    id: int

    class Config:
        from_attributes = True


class ShiftScheduleCreate(BaseModel):
    employee_id: int
    shift_date: date
    shift_type: str = Field(pattern="^(morning|evening|night|on_call)$")
    start_time: str
    end_time: str
    unit_type: str | None = None


class ShiftScheduleRead(ShiftScheduleCreate):
    id: int

    class Config:
        from_attributes = True


class OvertimeCreate(BaseModel):
    employee_id: int
    overtime_date: date
    hours: int = Field(ge=1, le=12)
    reason: str | None = None


class OvertimeApproval(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    approved_by: str


class OvertimeRead(BaseModel):
    id: int
    employee_id: int
    overtime_date: date
    hours: int
    reason: str | None
    status: str
    approved_by: str | None

    class Config:
        from_attributes = True


class RecruitmentPositionCreate(BaseModel):
    title: str
    department_id: int
    workforce_category: str = Field(pattern="^(nurse|medic|non_medic|support|other)$")
    open_date: date
    target_hire_date: date | None = None
    created_by: str


class RecruitmentPositionRead(BaseModel):
    id: int
    title: str
    department_id: int
    workforce_category: str
    open_date: date
    target_hire_date: date | None
    status: str
    created_by: str

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    position_id: int
    full_name: str
    email: EmailStr
    phone: str | None = None
    stage: str = "screening"
    score: int | None = Field(default=None, ge=0, le=100)


class CandidateStageUpdate(BaseModel):
    stage: str
    status: str = Field(pattern="^(active|hired|rejected|withdrawn)$")
    score: int | None = Field(default=None, ge=0, le=100)


class CandidateRead(BaseModel):
    id: int
    position_id: int
    full_name: str
    email: EmailStr
    phone: str | None
    stage: str
    score: int | None
    status: str

    class Config:
        from_attributes = True


class OnboardingTaskCreate(BaseModel):
    employee_id: int
    task_name: str
    due_date: date | None = None
    owner: str | None = None
    notes: str | None = None


class OnboardingTaskUpdate(BaseModel):
    status: str = Field(pattern="^(pending|in_progress|done)$")
    notes: str | None = None


class OnboardingTaskRead(BaseModel):
    id: int
    employee_id: int
    task_name: str
    due_date: date | None
    status: str
    owner: str | None
    notes: str | None

    class Config:
        from_attributes = True


class EmployeeGoalCreate(BaseModel):
    employee_id: int
    title: str
    description: str | None = None
    review_period: str
    target_value: int = Field(ge=1)
    current_value: int = Field(default=0, ge=0)
    linked_kpi_id: int | None = None
    created_by: str


class EmployeeGoalUpdate(BaseModel):
    current_value: int = Field(ge=0)
    status: str = Field(pattern="^(on_track|at_risk|achieved|not_achieved)$")


class EmployeeGoalRead(BaseModel):
    id: int
    employee_id: int
    title: str
    description: str | None
    review_period: str
    target_value: int
    current_value: int
    linked_kpi_id: int | None
    status: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecruitmentAnalyticsSummary(BaseModel):
    total_open_positions: int
    total_active_candidates: int
    candidates_hired: int
    candidates_rejected: int
    conversion_rate_percent: int
    onboarding_total_tasks: int
    onboarding_overdue_tasks: int
    onboarding_completed_tasks: int
    onboarding_sla_percent: int


class GoalKpiCalibrationSummary(BaseModel):
    review_period: str
    department_id: int
    employee_goal_count: int
    linked_goal_count: int
    avg_goal_progress_percent: int
    avg_kpi_score: int
    alignment_gap_count: int


class KpiCalibrationItemInput(BaseModel):
    review_id: int
    calibrated_score: int = Field(ge=0, le=200)
    rationale: str | None = None


class KpiCalibrationSessionCreate(BaseModel):
    department_id: int
    review_period: str
    created_by: str
    notes: str | None = None
    items: list[KpiCalibrationItemInput]


class KpiCalibrationSessionRead(BaseModel):
    id: int
    department_id: int
    review_period: str
    status: str
    created_by: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True
