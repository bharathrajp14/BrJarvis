from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RoleType(str, Enum):
    engineer = "engineer"
    designer = "designer"
    manager = "manager"
    sales = "sales"
    marketing = "marketing"
    hr = "hr"
    finance = "finance"
    operations = "operations"


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class TaskBase(BaseModel):
    title: str
    description: str
    due_day: int
    category: str


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: str
    status: TaskStatus = TaskStatus.pending
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleType
    department: str
    start_date: str


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    id: str
    tasks: List[Task] = []
    progress: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class OnboardingPlanRequest(BaseModel):
    employee_name: str
    role: RoleType
    department: str
    start_date: str
    company_name: str
    manager_name: Optional[str] = None
    custom_notes: Optional[str] = None


class OnboardingPlanResponse(BaseModel):
    employee_id: str
    plan_title: str
    tasks: List[Task]
    total_days: int
    ai_message: str


class TaskUpdateRequest(BaseModel):
    status: TaskStatus


class DashboardStats(BaseModel):
    total_employees: int
    active_onboardings: int
    completed_this_month: int
    avg_completion_rate: float
    recent_employees: List[Employee]
