# Sophisticated Hospital HRIS (Starter)

This repository now contains a robust backend starter for a **Hospital Human Resources Information System** with:

- JWT authentication
- Role-based access control (`admin`, `hr_manager`, `staff`)
- Department management
- Employee management
- Leave request workflow (submit + approve/reject)
- Regulatory compliance module for Indonesia (Bali scope)
- Training Needs Analysis (TNA) workflow for hospital workforce
- Workload Analysis with multi-model staffing calculations
- Balanced Scorecard and KPI management
- Payroll and tax processing baseline
- Attendance, shift, and overtime tracking
- Recruitment, candidates, and onboarding tasks
- Goal tracking linked to KPI
- SQLite persistence via SQLAlchemy

## 1) Setup

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run

```bash
uvicorn app.main:app --reload
```

API will be available at:

- `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

## 3) Default admin account

Seeded automatically on first start:

- Username: `admin`
- Password: `Admin123!`

## 4) Core endpoints

- `POST /auth/login` -> get JWT token
- `POST /auth/register` -> create user (admin only)
- `GET/POST /departments` -> list/create departments
- `GET/POST /employees` -> list/create employees
- `GET/POST /leave-requests` -> list/create leave requests
- `PATCH /leave-requests/{leave_id}/approval` -> approve/reject request
- `GET/POST /compliance/sources` -> official regulatory institutions
- `POST /compliance/sources/{source_id}/check` -> monitor one source for updates
- `POST /compliance/sources/check-all` -> monitor all active sources
- `GET/POST /compliance/rules` -> legal requirements tracker
- `GET/POST /compliance/checks` -> employee compliance checks
- `PATCH /compliance/checks/{check_id}/review` -> verify/reject documents
- `GET /compliance/logs` -> regulation monitoring history
- `GET /compliance/alerts` -> unresolved/resolved compliance alerts
- `GET /compliance/dashboard` -> executive compliance metrics
- `POST/GET /training-needs` -> create/list TNA records
- `PATCH /training-needs/{analysis_id}` -> update TNA record
- `PATCH /training-needs/{analysis_id}/verify` -> approve/reject TNA verification
- `POST/GET /workload-analysis` -> create/list workload analysis
- `POST /workload-analysis/{analysis_id}/refresh` -> recalculate and schedule next review
- `POST /workload-analysis/{analysis_id}/schedule` -> set weekly/monthly auto refresh
- `PATCH /workload-analysis/{analysis_id}/schedule` -> update schedule
- `GET /workload-analysis/schedules` -> monitor all schedules
- `POST /workload-analysis/scheduler/run-due` -> manual trigger due scheduler jobs
- `POST/GET /kpi/definitions` -> create/list KPI definitions
- `POST/GET /kpi/reviews` -> create/list KPI reviews
- `GET /kpi/reviews/{review_id}/items` -> KPI review item details
- `GET /kpi/balanced-scorecard/summary` -> BSC summary (overall + perspective)
- `POST/GET /payroll/profiles` -> employee payroll profile
- `POST /payroll/run` -> process payroll run
- `GET /payroll/run/{run_id}/items` -> payroll detail items
- `POST/GET /attendance/records` -> attendance records
- `POST/GET /attendance/shifts` -> shift schedule
- `POST/GET /attendance/overtime` -> overtime request/list
- `PATCH /attendance/overtime/{overtime_id}/approval` -> overtime approval
- `POST/GET /recruitment/positions` -> open positions
- `POST/GET /recruitment/candidates` -> candidate pipeline
- `PATCH /recruitment/candidates/{candidate_id}` -> update candidate stage
- `POST/GET /recruitment/onboarding/tasks` -> onboarding checklist
- `PATCH /recruitment/onboarding/tasks/{task_id}` -> onboarding task update
- `GET /recruitment/analytics/summary` -> recruitment funnel + onboarding SLA dashboard
- `POST/GET /goals` -> create and monitor employee goals
- `PATCH /goals/{goal_id}` -> update goal progress
- `GET /goals/calibration-summary` -> goal vs KPI alignment per unit/review period
- `POST/GET /kpi/calibration/sessions` -> KPI calibration workflow per unit

## 5) Indonesia (Bali) compliance scope

The compliance module is designed to track:

- central regulations from Kemenkes/Kemnaker and related ministries
- local regulations from Pemprov Bali and relevant dinas
- requirements for `tenaga_kesehatan` and `non_kesehatan`
- required documents, validity period, and verification status per employee

Default sources are seeded automatically at startup for Bali monitoring.

The monitor uses website content fingerprinting (hash-based) to detect source changes and generate alerts for compliance review.

## 6) Important legal note

Regulations in Indonesia can change frequently. This system helps operational tracking, but final legal interpretation should still be validated by your HR legal/compliance team before policy enforcement.

## 7) Training Needs Analysis (TNA)

This module supports hospital-focused TNA for workforce categories:

- `nurse`
- `medic`
- `non_medic`
- `support`
- `other`

Each TNA record includes competency gaps, regulation references, recommended training, target participant count, and verification flow (`approved` / `rejected`) by HR leadership.

## 8) Suggested next steps

To make this enterprise-grade, add:

1. Shift scheduling and attendance biometric integration.
2. Payroll engine (allowances, overtime, deductions, tax, payslips).
3. Recruitment and onboarding workflows.
4. Performance appraisal and credential tracking.
5. Audit log trails and report/dashboard module.
6. Scheduled background jobs for automatic workload refresh per unit.
7. Multi-tenant hospital branch support.

## 9) Workload analysis notes

Current workload models included:

- `hours_based`
- `ratio_based`
- `wisn_simplified`

This gives a practical baseline for Indonesian private hospital staffing analysis across `nurse`, `medic`, `non_medic`, and support teams, with regulation context fields and periodic refresh support.

Supported service types include:

- `igd`, `icu`, `ok`, `rawat_inap`, `rawat_jalan`, `farmasi`, `penunjang`, `administrasi`

Scheduler behavior:

- automatic due-job runner every hour (background scheduler)
- per-analysis weekly/monthly schedule
- management alerts generated when staffing gap is detected during scheduled refresh

Financial indicators (supporting signal only):

- optional inputs: revenue, EBITDA margin, cashflow coverage months
- system computes a `financial_pressure_index` and an `optimum_staff_count`
- safety rule: optimization will not go below minimum regulatory staffing
