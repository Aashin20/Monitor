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
