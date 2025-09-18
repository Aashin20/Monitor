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
