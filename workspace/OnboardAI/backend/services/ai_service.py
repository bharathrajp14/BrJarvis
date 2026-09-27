import openai
import os
from typing import Optional

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

def generate_onboarding_plan(role: str, department: str, company_name: str, duration_days: int = 30) -> dict:
    """
    Generate a personalized onboarding plan using GPT-4o
    """
    prompt = f"""
    Create a detailed {duration_days}-day employee onboarding plan for:
    - Role: {role}
    - Department: {department}
    - Company: {company_name}

    Return a JSON object with this structure:
    {{
        "overview": "brief overview string",
        "phases": [
            {{
                "name": "Phase name",
                "duration": "e.g. Week 1",
                "goals": ["goal1", "goal2"],
                "tasks": [
                    {{
                        "title": "Task title",
                        "description": "Task description",
                        "due_day": 1,
                        "priority": "high/medium/low",
                        "category": "admin/training/social/technical"
                    }}
                ]
            }}
        ],
        "resources": ["resource1", "resource2"],
        "success_metrics": ["metric1", "metric2"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert HR consultant specializing in employee onboarding. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # Fallback plan if API fails
        return {
            "overview": f"Standard onboarding plan for {role} in {department}",
            "phases": [
                {
                    "name": "Week 1: Orientation",
                    "duration": "Days 1-7",
                    "goals": ["Meet the team", "Set up workstation", "Understand company culture"],
                    "tasks": [
                        {"title": "Complete HR paperwork", "description": "Fill all required forms", "due_day": 1, "priority": "high", "category": "admin"},
                        {"title": "IT setup", "description": "Get laptop, accounts, and access", "due_day": 1, "priority": "high", "category": "technical"},
                        {"title": "Meet your manager", "description": "1:1 intro meeting", "due_day": 2, "priority": "high", "category": "social"},
                        {"title": "Team introduction", "description": "Meet all team members", "due_day": 3, "priority": "medium", "category": "social"}
                    ]
                },
                {
                    "name": "Week 2-4: Learning",
                    "duration": "Days 8-30",
                    "goals": ["Learn core tools", "Complete training modules", "First project"],
                    "tasks": [
                        {"title": "Complete product training", "description": "Go through all training materials", "due_day": 14, "priority": "high", "category": "training"},
                        {"title": "Shadow a colleague", "description": "Observe day-to-day workflow", "due_day": 10, "priority": "medium", "category": "training"},
                        {"title": "First deliverable", "description": "Complete first assigned task", "due_day": 30, "priority": "high", "category": "technical"}
                    ]
                }
            ],
            "resources": ["Employee Handbook", "Company Wiki", "Team Slack Channel"],
            "success_metrics": ["Complete all tasks on time", "Pass product knowledge quiz", "Positive 30-day review"]
        }

def generate_welcome_email(employee_name: str, role: str, company_name: str, start_date: str) -> str:
    """
    Generate a personalized welcome email
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an HR professional writing warm, professional welcome emails."},
                {"role": "user", "content": f"Write a welcome email for {employee_name} joining as {role} at {company_name} on {start_date}. Keep it warm, professional, and encouraging. Include what they can expect on day 1."}
            ],
            temperature=0.8
        )
        return response.choices[0].message.content
    except:
        return f"""Dear {employee_name},

Welcome to {company_name}! We are thrilled to have you join us as {role} starting {start_date}.

On your first day, you can expect:
- A warm welcome from your team
- IT setup and account creation
- Meeting with your manager
- Office/virtual tour

We look forward to seeing you grow with us!

Best regards,
The HR Team at {company_name}"""
