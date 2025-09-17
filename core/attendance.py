from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from utils.db import Database
from models import AttendanceSession, ClassSchedule, User, UserRole,StudentCourseEnrollment, AttendanceStatus, AttendanceRecord
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from core.reg_attendance import clear_session_cache
from utils.mail import send_email

def create_attendance_session(
    faculty_id: str,
    lat: float,
    lon: float,
    radius_meters: int,
    remarks: str = None
) -> dict:
    try:
        clear_session_cache()
        with Database.get_session() as session:
            faculty = session.query(User).filter_by(reg_no=faculty_id).first()
            if not faculty:
                return {"success": False, "message": "Faculty not found"}

            if faculty.role != UserRole.faculty:
                return {"success": False, "message": "User is not a faculty member"}

            schedule = session.query(ClassSchedule).filter(
                and_(
                    ClassSchedule.faculty_id == faculty_id,
                    ClassSchedule.is_active
                )
            ).first()

            if not schedule:
                return {
                    "success": False,
                    "message": "No active class schedule found for this faculty"
                }

            course = schedule.course
            if not course:
                return {"success": False, "message": "Course not found for schedule"}

            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)

            existing_session = session.query(AttendanceSession).filter(
                and_(
                    AttendanceSession.faculty_id == faculty_id,
                    AttendanceSession.course_id == schedule.course_id,
                    AttendanceSession.start_time >= today_start,
                    AttendanceSession.start_time < today_end,
                    AttendanceSession.is_active
                )
            ).first()

            if existing_session:
                return {
                    "success": False,
                    "message": "An active attendance session already exists for this course today"
                }

            start_time = datetime.now()

            attendance_session = AttendanceSession(
                course_id=schedule.course_id,
                faculty_id=faculty_id,
                start_time=start_time,
                lat=lat,
                long=lon,
                radius_meters=radius_meters,
                is_active=True,
                remarks=remarks,
                schedule_id=schedule.id
            )

            session.add(attendance_session)
            session.commit()

            return {
                "success": True,
                "message": f"Attendance session created successfully for {course.course_name}",
                "session_id": attendance_session.id,
                "course_name": course.course_name,
                "course_code": course.course_code,
                "classroom": schedule.classroom.class_number,
                "time_slot": f"{schedule.time_slot.start_time}-{schedule.time_slot.end_time}",
            }

    except SQLAlchemyError as e:
        return {"success": False, "message": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
    


def get_attendance_summary():
    try:
        with Database.get_session() as session:
            attendance_session = (
                session.query(AttendanceSession)
                .options(joinedload(AttendanceSession.course))
                .filter_by(is_active=True)
                .first()
            )

            if not attendance_session:
                return {"success": False, "message": "No active attendance session found"}

            course_id = attendance_session.course_id
            session_id = attendance_session.id

            total_students = (
                session.query(StudentCourseEnrollment)
                .filter_by(course_id=course_id)
                .count()
            )

            present_records = (
                session.query(AttendanceRecord)
                .join(User)
                .filter(
                    AttendanceRecord.session_id == session_id,
                    AttendanceRecord.status == AttendanceStatus.present
                )
                .all()
            )

            present_roll_numbers = [record.student.reg_no for record in present_records]

            return {
                "session_id": session_id,
                "course_id": course_id,
                "present_roll_numbers": present_roll_numbers,
                "present_count": len(present_roll_numbers),
                "total_students": total_students
            }

    except SQLAlchemyError as e:
        return {"success": False, "message": f"Database error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
