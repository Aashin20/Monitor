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
