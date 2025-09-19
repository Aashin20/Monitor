from pydantic import BaseModel,Base64Bytes
from fastapi import APIRouter
from core.attendance import create_attendance_session
from core.reg_attendance import register_attendance
from core.attendance import get_attendance_summary, end_attendance_session
from fastapi import  HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc
import csv
import os
import tempfile
from utils.db import Database
from fastapi import BackgroundTasks
from models import (
    AttendanceSession, AttendanceRecord, User, Course, 
    StudentCourseEnrollment, AttendanceStatus
)

router = APIRouter()

class AttendanceSessionCreate(BaseModel):
    faculty_id: str
    lat: float
    lon: float
    radius_meters: int
    remarks: str = None

class RegisterAttendance(BaseModel):
    student_id: str
    face: Base64Bytes
    lat: float
    lon: float

@router.post("/session/create")
async def create_session(details: AttendanceSessionCreate):
    return create_attendance_session(
        faculty_id=details.faculty_id,
        lat=details.lat,
        lon=details.lon,
        radius_meters=details.radius_meters,
        remarks=details.remarks
    )

@router.post("/student/register")
async def reg_attendance(details: RegisterAttendance):
    return register_attendance(
        student_id=details.student_id,
        face_image_bytes=details.face,
        student_latitude=details.lat,
        student_longitude=details.lon
    )

@router.get("/session/summary")
async def get_session_summary():
    return get_attendance_summary()

@router.post("/session/end/{faculty_id}")
async def end_session(faculty_id: str):
    return end_attendance_session(faculty_id)

@router.get("/csv")
async def export_latest_attendance_csv(background_tasks: BackgroundTasks):

    try:
        with Database.get_session() as db:
            latest_session = db.query(AttendanceSession).order_by(
                AttendanceSession.start_time.desc()
            ).first()
            
            if not latest_session:
                raise HTTPException(status_code=404, detail="No attendance session found")
            
            enrolled_students = db.query(User).join(
                StudentCourseEnrollment, 
                User.reg_no == StudentCourseEnrollment.student_id
            ).filter(
                StudentCourseEnrollment.course_id == latest_session.course_id
            ).all()
            
            attendance_records = db.query(AttendanceRecord).filter(
                AttendanceRecord.session_id == latest_session.id
            ).all()
            
            attendance_dict = {record.student_id: record for record in attendance_records}
            
            course = db.query(Course).filter(Course.id == latest_session.course_id).first()
            faculty = db.query(User).filter(User.reg_no == latest_session.faculty_id).first()
            
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
            
            try:
                writer = csv.writer(temp_file)
                
                writer.writerow(['Attendance Report'])
                writer.writerow(['Course:', f"{course.course_name} ({course.course_code})" if course else "N/A"])
                writer.writerow(['Faculty:', faculty.name if faculty else "N/A"])
                writer.writerow(['Session Date:', "16/09/2025"])
                
                present_count = 0
                absent_count = 0
                late_count = 0
                
                writer.writerow([
                    'Registration No', 
                    'Student Name', 
                    'Attendance Status', 
                    'Timestamp'
                ])
                
                for student in enrolled_students:
                    if student.reg_no in attendance_dict:
                        record = attendance_dict[student.reg_no]
                        timestamp = record.timestamp.strftime('%Y-%m-%d %H:%M:%S') if record.timestamp else "N/A"
                        
                        writer.writerow([
                            student.reg_no,
                            student.name,
                            record.status.value.title(),
                            timestamp
                        ])
                        
                        if record.status == AttendanceStatus.present:
                            present_count += 1
                        elif record.status == AttendanceStatus.absent:
                            absent_count += 1
                        elif record.status == AttendanceStatus.late:
                            late_count += 1
                    else:
                        writer.writerow([
                            student.reg_no,
                            student.name,
                            'Absent',
                            'N/A'
                        ])
                        absent_count += 1
                
                writer.writerow([])  
                writer.writerow(['Summary:'])
                writer.writerow(['Total Students:', len(enrolled_students)])
                writer.writerow(['Present:', present_count])
                writer.writerow(['Late:', late_count])
                writer.writerow(['Absent:', absent_count])
                writer.writerow(['Attendance Percentage:', f"{((present_count + late_count) / len(enrolled_students) * 100):.2f}%" if enrolled_students else "0%"])
                
                temp_file.close()
                
                filename = f"attendance_report_{course.course_code if course else 'unknown'}_{latest_session.start_time.strftime('%Y%m%d_%H%M%S')}.csv"
                
                background_tasks.add_task(cleanup_temp_file, temp_file.name)
                
                return FileResponse(
                    path=temp_file.name,
                    filename=filename,
                    media_type='application/octet-stream',
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
                
            except Exception as e:
                os.unlink(temp_file.name)
                raise e
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating CSV: {str(e)}")


def cleanup_temp_file(file_path: str):
    try:
        os.unlink(file_path)
    except OSError:
        pass