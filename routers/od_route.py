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


@router.post("/submit", response_model=APIResponse)
async def submit_leave_request_endpoint(request: LeaveRequestCreate):
    """
    Submit a new leave request from student
    """
    try:
        result = submit_leave_request(
            student_id=request.student_id,
            start_date=request.start_date,
            end_date=request.end_date,
            reason=request.reason,
            attachment_url=request.attachment_url
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return APIResponse(
            success=True,
            message=result["message"],
            data={"request_id": result.get("request_id")}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/faculty/{faculty_id}", response_model=APIResponse)
async def view_leave_requests_endpoint(faculty_id: str):
    """
    View all leave requests for faculty review
    """
    try:
        result = view_leave_requests(faculty_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return APIResponse(
            success=True,
            message=result["message"],
            data={"requests": result["requests"]}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{request_id}/process", response_model=APIResponse)
async def process_leave_request_endpoint(request_id: int, request: LeaveRequestProcess):
    """
    Process (approve/reject) a leave request by faculty
    """
    try:
        result = process_leave_request(
            request_id=request_id,
            faculty_id=request.faculty_id,
            action=request.action,
            remarks=request.remarks
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return APIResponse(
            success=True,
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/student/{student_id}", response_model=APIResponse)
async def get_student_leave_requests(student_id: str):
    """
    Get all leave requests for a specific student
    """
    try:
        from utils.db import Database
        from models import LeaveRequest, User
        
        with Database.get_session() as session:
            student = session.query(User).filter_by(reg_no=student_id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )
            
            requests = session.query(LeaveRequest).filter_by(student_id=student_id).all()
            
            requests_data = []
            for req in requests:
                requests_data.append({
                    "id": req.id,
                    "start_date": req.start_date,
                    "end_date": req.end_date,
                    "reason": req.reason,
                    "status": req.status.value,
                    "attachment_url": req.attachment_url,
                    "created_at": req.created_at,
                    "faculty_remarks": req.faculty_remarks,
                    "reviewed_by": req.reviewed_by_faculty_id
                })
        
        return APIResponse(
            success=True,
            message="Leave requests retrieved successfully",
            data={"requests": requests_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/pending", response_model=APIResponse)
async def get_pending_leave_requests():
    """
    Get all pending leave requests (for admin/faculty dashboard)
    """
    try:
        from utils.db import Database
        from models import LeaveRequest, User, LeaveStatus
        
        with Database.get_session() as session:
            pending_requests = session.query(LeaveRequest).join(
                User, LeaveRequest.student_id == User.reg_no
            ).filter(LeaveRequest.status == LeaveStatus.pending).all()
            
            requests_data = []
            for req in pending_requests:
                requests_data.append({
                    "id": req.id,
                    "student_id": req.student_id,
                    "student_name": req.student.name,
                    "start_date": req.start_date,
                    "end_date": req.end_date,
                    "reason": req.reason,
                    "status": req.status.value,
                    "attachment_url": req.attachment_url,
                    "created_at": req.created_at
                })
        
        return APIResponse(
            success=True,
            message="Pending leave requests retrieved successfully",
            data={"requests": requests_data}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


