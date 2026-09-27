from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import openai
import os

router = APIRouter()

class OnboardingRequest(BaseModel):
    employee_name: str
    role: str
    department: str
    start_date: str
    manager_name: Optional[str] = None

class Task(BaseModel):
    id: int
    title: str
    description: str
    day: int
    category: str
    completed: bool = False

class OnboardingPlan(BaseModel):
    employee_name: str
    role: str
    department: str
    start_date: str
    tasks: List[Task]
    welcome_message: str

@router.post('/generate', response_model=OnboardingPlan)
async def generate_onboarding_plan(request: OnboardingRequest):
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'demo-key'))
        
        prompt = f"""
Create a detailed 30-day onboarding plan for:
- Employee: {request.employee_name}
- Role: {request.role}
- Department: {request.department}
- Start Date: {request.start_date}
- Manager: {request.manager_name or 'TBD'}

Return a JSON object with:
1. welcome_message (personalized, motivating)
2. tasks array with 15 tasks, each having: id, title, description, day (1-30), category (Setup/Training/Social/Admin), completed (false)

Make tasks specific to the role and department.
"""
        
        # Demo mode - return sample plan if no API key
        if os.getenv('OPENAI_API_KEY', 'demo-key') == 'demo-key':
            return _get_demo_plan(request)
            
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'}
        )
        
        import json
        data = json.loads(response.choices[0].message.content)
        
        tasks = [Task(**t) for t in data.get('tasks', [])]
        
        return OnboardingPlan(
            employee_name=request.employee_name,
            role=request.role,
            department=request.department,
            start_date=request.start_date,
            tasks=tasks,
            welcome_message=data.get('welcome_message', f'Welcome {request.employee_name}!')
        )
    except Exception as e:
        return _get_demo_plan(request)

def _get_demo_plan(request: OnboardingRequest) -> OnboardingPlan:
    tasks = [
        Task(id=1, title='Set up workstation', description='Configure laptop, install required software', day=1, category='Setup'),
        Task(id=2, title='Meet your team', description='Introduction calls with all team members', day=1, category='Social'),
        Task(id=3, title='Review company handbook', description='Read through company policies and culture docs', day=2, category='Admin'),
        Task(id=4, title='Set up email & Slack', description='Configure communication tools and join channels', day=1, category='Setup'),
        Task(id=5, title='HR paperwork', description='Complete all required HR documents and benefits enrollment', day=2, category='Admin'),
        Task(id=6, title='Role-specific training Day 1', description=f'Begin {request.role} fundamentals training', day=3, category='Training'),
        Task(id=7, title='Meet with manager', description='1:1 with manager to discuss goals and expectations', day=3, category='Social'),
        Task(id=8, title='Product demo', description='Watch full product walkthrough and demos', day=4, category='Training'),
        Task(id=9, title='Shadow a colleague', description='Spend a day shadowing an experienced team member', day=5, category='Training'),
        Task(id=10, title='First project assignment', description='Receive and begin first real project', day=7, category='Training'),
        Task(id=11, title='Week 2 check-in', description='Review progress with manager', day=10, category='Admin'),
        Task(id=12, title='Customer/stakeholder intro', description='Meet key customers or internal stakeholders', day=14, category='Social'),
        Task(id=13, title='Advanced role training', description='Complete advanced training modules', day=21, category='Training'),
        Task(id=14, title='30-day review', description='Performance and progress review with manager', day=30, category='Admin'),
        Task(id=15, title='Set 90-day goals', description='Define personal OKRs for first 90 days', day=30, category='Admin'),
    ]
    return OnboardingPlan(
        employee_name=request.employee_name,
        role=request.role,
        department=request.department,
        start_date=request.start_date,
        tasks=tasks,
        welcome_message=f'Welcome to the team, {request.employee_name}! We are thrilled to have you as our new {request.role}. Your first 30 days are carefully planned to help you hit the ground running. Let us make this an amazing journey together!'
    )

@router.get('/plans')
async def list_plans():
    return {'plans': [], 'message': 'Connect to database to see plans'}

@router.get('/plan/{plan_id}')
async def get_plan(plan_id: str):
    return {'id': plan_id, 'status': 'active'}
