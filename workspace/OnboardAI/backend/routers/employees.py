from fastapi import APIRouter, HTTPException
from typing import List
from models.employee import Employee, EmployeeCreate
from services.ai_service import AIService
import uuid
from datetime import datetime

router = APIRouter()
ai_service = AIService()

# In-memory store (replace with DB in production)
employees_db = {}

@router.get("/", response_model=List[Employee])
async def list_employees():
    return list(employees_db.values())

@router.post("/", response_model=Employee)
async def create_employee(employee: EmployeeCreate):
    emp_id = str(uuid.uuid4())
    new_employee = Employee(
        id=emp_id,
        name=employee.name,
        email=employee.email,
        role=employee.role,
        department=employee.department,
        start_date=employee.start_date,
        progress=0,
        status="pending",
        created_at=datetime.utcnow().isoformat()
    )
    employees_db[emp_id] = new_employee
    return new_employee

@router.get("/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    if employee_id not in employees_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employees_db[employee_id]

@router.patch("/{employee_id}/progress")
async def update_progress(employee_id: str, progress: int):
    if employee_id not in employees_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    employees_db[employee_id].progress = progress
    if progress >= 100:
        employees_db[employee_id].status = "completed"
    elif progress > 0:
        employees_db[employee_id].status = "active"
    return {"message": "Progress updated", "progress": progress}

@router.delete("/{employee_id}")
async def delete_employee(employee_id: str):
    if employee_id not in employees_db:
        raise HTTPException(status_code=404, detail="Employee not found")
    del employees_db[employee_id]
    return {"message": "Employee deleted successfully"}
