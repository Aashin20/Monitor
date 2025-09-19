from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List
from core.od import (
    submit_leave_request, 
    view_leave_requests, 
    process_leave_request
)

router = APIRouter()


class LeaveRequestCreate(BaseModel):
    student_id: str
    start_date: datetime
    end_date: datetime
    reason: str
    attachment_url: Optional[str] = None

    @validator('reason')
    def validate_reason(cls, v):
        if not v.strip():
            raise ValueError('Reason cannot be empty')
        return v.strip()


class LeaveRequestProcess(BaseModel):
    faculty_id: str
    action: str  # 'approve' or 'reject'
    remarks: Optional[str] = None

    @validator('action')
    def validate_action(cls, v):
        if v.lower() not in ['approve', 'reject']:
            raise ValueError('Action must be approve or reject')
        return v.lower()


class LeaveRequestResponse(BaseModel):
    id: int
    student_id: str
    student_name: str
    start_date: datetime
    end_date: datetime
    reason: str
    status: str
    attachment_url: Optional[str]
    created_at: datetime
    faculty_remarks: Optional[str]


class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

