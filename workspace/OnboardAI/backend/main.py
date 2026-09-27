from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import onboarding, employees, analytics

app = FastAPI(
    title="OnboardAI API",
    description="AI-Powered Employee Onboarding Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(onboarding.router, prefix="/api/onboarding", tags=["Onboarding"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "OnboardAI API is running!", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
