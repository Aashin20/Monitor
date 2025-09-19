from fastapi import APIRouter
from core.dashboard import get_student_timetable,get_faculty_attendance_history

router =  APIRouter()

@router.get("/timetable/{student_reg_no}")
async def fetch_timetable(student_reg_no: str):           
    return get_student_timetable(student_reg_no)

@router.get("/faculty/{faculty_id}")
async def fetch_faculty_history(faculty_id: str):   
    return get_faculty_attendance_history(faculty_id)