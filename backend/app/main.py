from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inquiries, onboarding, billing, payments, moveouts, tenant, faq, monitoring, dashboard, auth, residents, moveins, miscellaneous, service_requests
import os

app = FastAPI(
    title="Dormtel Automation API",
    description="End-to-end dormitory operations automation",
    version="1.0.0"
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inquiries.router, prefix="/api/v1/inquiries", tags=["inquiries"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(billing.router, prefix="/api/v1/billings", tags=["billings"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(moveouts.router, prefix="/api/v1/moveouts", tags=["moveouts"])
app.include_router(tenant.router, prefix="/api/v1/tenant", tags=["tenant-portal"])
app.include_router(faq.router, prefix="/api/v1/faqs", tags=["faqs"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(residents.router, prefix="/api/v1/residents", tags=["residents"])
app.include_router(moveins.router, prefix="/api/v1/moveins", tags=["moveins"])
app.include_router(miscellaneous.router, prefix="/api/v1/miscellaneous", tags=["miscellaneous"])
app.include_router(service_requests.router, prefix="/api/v1/service-requests", tags=["service-requests"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dormtel-api"}
