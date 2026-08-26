"""
HR System Tool — MCP tool stub.

In production this would call Workday, SAP SuccessFactors, or similar
HRIS system to query employee information, benefits, leave, and payroll.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

# Simulated employee store
_EMPLOYEES = {
    "EMP-1234": {
        "employee_id": "EMP-1234", "name": "Sarah Johnson", "department": "Retail Banking",
        "position": "Branch Manager", "hire_date": "2018-03-15", "location": "New York HQ",
        "employment_status": "active", "manager": "VP of Retail Banking",
        "annual_leave_accrued": 22, "sick_leave_accrued": 10,
    },
    "EMP-5678": {
        "employee_id": "EMP-5678", "name": "Michael Chen", "department": "IT",
        "position": "Senior Developer", "hire_date": "2020-07-01", "location": "San Francisco",
        "employment_status": "active", "manager": "Director of Engineering",
        "annual_leave_accrued": 18, "sick_leave_accrued": 12,
    },
    "EMP-9012": {
        "employee_id": "EMP-9012", "name": "Emily Rodriguez", "department": "Compliance",
        "position": "Compliance Officer", "hire_date": "2019-01-10", "location": "New York HQ",
        "employment_status": "active", "manager": "Chief Compliance Officer",
        "annual_leave_accrued": 20, "sick_leave_accrued": 11,
    },
}


async def lookup_employee(identifier: str) -> dict:
    """
    Look up an employee by ID, name, or email.
    """
    # Search by ID
    if identifier in _EMPLOYEES:
        return _EMPLOYEES[identifier]

    # Search by name
    for emp in _EMPLOYEES.values():
        if identifier.lower() in emp["name"].lower():
            return emp

    return {"error": f"Employee not found: {identifier}"}


async def get_leave_balance(employee_id: str) -> dict:
    """Get an employee's current leave balances."""
    emp = _EMPLOYEES.get(employee_id)
    if not emp:
        return {"error": f"Employee not found: {employee_id}"}

    return {
        "employee_id": employee_id,
        "name": emp["name"],
        "annual_leave_days": emp["annual_leave_accrued"],
        "sick_leave_days": emp["sick_leave_accrued"],
        "personal_leave_days": 3,
        "as_of_date": datetime.utcnow().strftime("%Y-%m-%d"),
    }


async def get_benefits_info(employee_id: str) -> dict:
    """Get an employee's benefits enrollment information."""
    emp = _EMPLOYEES.get(employee_id)
    if not emp:
        return {"error": f"Employee not found: {employee_id}"}

    return {
        "employee_id": employee_id,
        "name": emp["name"],
        "benefits": {
            "health_insurance": "PPO Plan - Employee + Spouse",
            "dental": "Standard Dental",
            "vision": "Standard Vision",
            "401k": "8% contribution, employer match 4%",
            "life_insurance": "2x annual salary",
            "disability": "60% salary, 180-day elimination",
            "hsa": "$500 annual employer contribution",
            "fsa": "$2,000 annual election",
        },
        "open_enrollment_next": "November 1-30, 2024",
    }


async def get_org_chart(department: str | None = None) -> dict:
    """Get organizational chart information."""
    departments = {}
    for emp in _EMPLOYEES.values():
        dept = emp["department"]
        if department and dept != department:
            continue
        if dept not in departments:
            departments[dept] = []
        departments[dept].append({
            "employee_id": emp["employee_id"],
            "name": emp["name"],
            "position": emp["position"],
        })

    return {
        "departments": departments,
        "total_employees": len(_EMPLOYEES),
    }
