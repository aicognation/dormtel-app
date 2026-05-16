from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import inquiries, onboarding, billing, payments, moveouts

app = FastAPI(
    title="Dormtel Automation API",
    description="End-to-end dormitory operations automation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inquiries.router, prefix="/api/v1/inquiries", tags=["inquiries"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(billing.router, prefix="/api/v1/billings", tags=["billings"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(moveouts.router, prefix="/api/v1/moveouts", tags=["moveouts"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dormtel-api"}
