from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import (
    User, LeaveRequest, LeaveStatus, AttendanceSession, 
    AttendanceRecord, AttendanceStatus, StudentCourseEnrollment
)
from utils.db import Database
from datetime import datetime, timezone

def submit_leave_request(student_id: str, start_date: datetime, end_date: datetime, reason: str, attachment_url: str = None):

    try:
        with Database.get_session() as session:
            student = session.query(User).filter_by(reg_no=student_id).first()
            if not student:
                return {"success": False, "message": "Student not found"}
            
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)

            if start_date >= end_date:
                return {"success": False, "message": "End date must be after start date"}
            
            if start_date < now:
                return {"success": False, "message": "Start date cannot be in the past"}
            
            leave_request = LeaveRequest(
                student_id=student_id,
                start_date=start_date,
                end_date=end_date,
                reason=reason,
                attachment_url=attachment_url,
                status=LeaveStatus.pending
            )
            
            session.add(leave_request)
            session.commit()
            
            return {
                "success": True, 
                "message": "Leave request submitted successfully",
                "request_id": leave_request.id
            }
            
    except Exception as e:
        return {"success": False, "message": f"Error submitting leave request: {str(e)}"}


def view_leave_requests(faculty_id: str):
    """
    View all pending and processed leave requests from faculty side
    """
    try:
        with Database.get_session() as session:
            faculty = session.query(User).filter_by(reg_no=faculty_id).first()
            if not faculty:
                return {"success": False, "message": "Faculty not found"}
            
            requests = session.query(LeaveRequest).join(User, LeaveRequest.student_id == User.reg_no).all()
            
            requests_data = []
            for req in requests:
                requests_data.append({
                    "id": req.id,
                    "student_id": req.student_id,
                    "student_name": req.student.name,
                    "start_date": req.start_date,
                    "end_date": req.end_date,
                    "reason": req.reason,
                    "status": req.status.value,
                    "attachment_url": req.attachment_url,
                    "created_at": req.created_at,
                    "faculty_remarks": req.faculty_remarks
                })
            
            return {
                "success": True,
                "message": "Leave requests retrieved successfully",
                "requests": requests_data
            }
            
    except Exception as e:
        return {"success": False, "message": f"Error retrieving leave requests: {str(e)}"}


def process_leave_request(request_id: int, faculty_id: str, action: str, remarks: str = None):
    """
    Accept or reject leave request from faculty side
    action should be 'approve' or 'reject'
    """
    try:
        with Database.get_session() as session:
            faculty = session.query(User).filter_by(reg_no=faculty_id).first()
            if not faculty:
                return {"success": False, "message": "Faculty not found"}
            
            leave_request = session.query(LeaveRequest).filter_by(id=request_id).first()
            if not leave_request:
                return {"success": False, "message": "Leave request not found"}
            
            if leave_request.status != LeaveStatus.pending:
                return {"success": False, "message": "Leave request already processed"}
            
            if action.lower() not in ['approve', 'reject']:
                return {"success": False, "message": "Action must be 'approve' or 'reject'"}
            
            if action.lower() == 'approve':
                leave_request.status = LeaveStatus.approved
                mark_result = mark_attendance_for_leave(leave_request.student_id, 
                                                     leave_request.start_date, 
                                                     leave_request.end_date,
                                                     session)
                if not mark_result["success"]:
                    return mark_result
            else:
                leave_request.status = LeaveStatus.rejected
            
            leave_request.reviewed_by_faculty_id = faculty_id
            leave_request.faculty_remarks = remarks
            
            session.commit()
            
            return {
                "success": True,
                "message": f"Leave request {action.lower()}d successfully"
            }
            
    except Exception as e:
        return {"success": False, "message": f"Error processing leave request: {str(e)}"}

