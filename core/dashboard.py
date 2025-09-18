from sqlalchemy.orm import joinedload
from utils.db import Database
from models import (StudentCourseEnrollment, Course, ClassSchedule,
                    AttendanceRecord,AttendanceSession,AttendanceStatus)
from collections import defaultdict

def get_student_timetable(student_reg_no: str):
    with Database.get_session() as session:
        enrollments = (
            session.query(StudentCourseEnrollment)
            .options(
                joinedload(StudentCourseEnrollment.course)
                .joinedload(Course.schedules)
                .joinedload(ClassSchedule.faculty),
                joinedload(StudentCourseEnrollment.course)
                .joinedload(Course.schedules)
                .joinedload(ClassSchedule.classroom),
                joinedload(StudentCourseEnrollment.course)
                .joinedload(Course.schedules)
                .joinedload(ClassSchedule.time_slot),
            )
            .filter(StudentCourseEnrollment.student_id == student_reg_no)
            .all()
        )

        day_map = {
            "monday": 15,
            "tuesday": 16,
            "wednesday": 17,
            "thursday": 18,
            "friday": 19,
            "saturday": 20,
            "sunday": 21, 
        }

        timetable = defaultdict(list)

        for enrollment in enrollments:
            for schedule in enrollment.course.schedules:
                if not schedule.is_active:
                    continue

                day_num = day_map[schedule.day_of_week.value]

                start = schedule.time_slot.start_time.strftime("%I:%M %p")
                end = schedule.time_slot.end_time.strftime("%I:%M %p")

                timetable[day_num].append({
                    "time": start,
                    "subject": schedule.course.course_name,
                    "duration": f"{start} - {end}",
                    "type": schedule.class_type.value
                })

        for d in day_map.values():
            timetable[d] = sorted(timetable[d], key=lambda x: x["time"])

        return dict(timetable)

def get_faculty_attendance_history(faculty_id: str):
    with Database.get_session() as session:
        sessions = (
            session.query(AttendanceSession)
            .filter(AttendanceSession.faculty_id == faculty_id)
            .order_by(AttendanceSession.start_time.desc())
            .all()
        )

        history = []
        for s in sessions:
            course = session.query(Course).filter(Course.id == s.course_id).first()
            if not course:
                continue

            records = (
                session.query(AttendanceRecord)
                .filter(AttendanceRecord.session_id == s.id)
                .all()
            )

            total = len(records)
            present = sum(1 for r in records if r.status == AttendanceStatus.present)

            date_str = s.start_time.strftime("%b %d")  # e.g., "Sep 10"
            if s.end_time:
                time_str = f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')}"
            else:
                time_str = s.start_time.strftime("%I:%M %p")

            history.append({
                "id": s.id,
                "date": date_str,
                "subject": course.course_name,
                "time": time_str,
                "present": present,
                "total": total
            })

        return history

