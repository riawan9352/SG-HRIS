from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.models import RegulationSource, User
from app.routers import (
    attendance,
    auth,
    compliance,
    departments,
    employees,
    goals,
    kpi,
    leave_requests,
    payroll,
    recruitment,
    training_needs,
    workload_analysis,
)
from app.services.scheduler_runtime import start_scheduler, stop_scheduler

app = FastAPI(title="Hospital HRIS API", version="0.1.0")

Base.metadata.create_all(bind=engine)


def seed_admin() -> None:
    db: Session = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            db.add(
                User(
                    username="admin",
                    full_name="System Administrator",
                    email="admin@hospital.local",
                    password_hash=get_password_hash("Admin123!"),
                    role="admin",
                )
            )
            db.commit()
    finally:
        db.close()


def seed_regulation_sources() -> None:
    db: Session = SessionLocal()
    try:
        default_sources = [
            (
                "Kementerian Kesehatan RI",
                "kemenkes",
                "https://www.kemkes.go.id",
            ),
            (
                "Kementerian Ketenagakerjaan RI",
                "kemenaker",
                "https://kemnaker.go.id",
            ),
            (
                "Dinas Kesehatan Provinsi Bali",
                "dinas_terkait",
                "https://diskes.baliprov.go.id",
            ),
            (
                "Dinas Tenaga Kerja dan ESDM Bali",
                "dinas_terkait",
                "https://disnakeresdm.baliprov.go.id",
            ),
            (
                "Pemerintah Provinsi Bali",
                "pemerintah_daerah",
                "https://www.baliprov.go.id",
            ),
        ]
        for name, level, url in default_sources:
            exists = db.query(RegulationSource).filter(RegulationSource.name == name).first()
            if not exists:
                db.add(
                    RegulationSource(
                        name=name,
                        institution_level=level,
                        website_url=url,
                        region_scope="Bali",
                    )
                )
        db.commit()
    finally:
        db.close()


seed_admin()
seed_regulation_sources()

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(leave_requests.router)
app.include_router(attendance.router)
app.include_router(payroll.router)
app.include_router(recruitment.router)
app.include_router(compliance.router)
app.include_router(training_needs.router)
app.include_router(workload_analysis.router)
app.include_router(kpi.router)
app.include_router(goals.router)


@app.on_event("startup")
def on_startup() -> None:
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    stop_scheduler()


@app.get("/")
def health_check():
    return {"message": "Hospital HRIS API is running"}
