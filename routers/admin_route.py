from fastapi import APIRouter
from core.courses import (create_course,enroll_students_to_course,
                          assign_faculty_to_course,get_course_info,create_class_schedule)
from core.admin import create_classroom,create_time_slot
from typing import List,Optional
from pydantic import BaseModel
from models import DayOfWeek, ClassType

router = APIRouter()

class CreateSchedule(BaseModel):
    course_code: str
    faculty_reg_no: str
    classroom_number: str
    time_slot_name: str
    day_of_week: DayOfWeek
    class_type: ClassType
    section: Optional[str] = None
    notes: Optional[str] = None

@router.post("/course/create")
async def course_create(course_name: str, course_code: str,credits: int,department: str):
    return create_course(course_name, course_code,credits,department)

@router.post("/course/enroll")
async def enroll_students(course_id: int, student_reg_nos: List[str]):
    return enroll_students_to_course(course_id, student_reg_nos)

@router.post("/course/assign")
async def assign_faculty(course_id: int, faculty_reg_nos: List[str]):
    return assign_faculty_to_course(course_id, faculty_reg_nos)

@router.get("/course/{course_id}")
async def course_info(course_id: int):
    return get_course_info(course_id)

@router.post("/course/schedule/create")
async def schedule_class(details: CreateSchedule):
    return create_class_schedule(
        course_code=details.course_code,
        faculty_reg_no=details.faculty_reg_no,
        classroom_number=details.classroom_number,
        time_slot_name=details.time_slot_name,
        day_of_week=details.day_of_week,
        class_type=details.class_type,
        section=details.section,
        notes=details.notes
    )

@router.post("/classroom/create")
async def classroom_create(class_number: str):
    return create_classroom(class_number)   
