import face_recognition
import numpy as np
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from utils.db import Database
from models import AttendanceSession, AttendanceRecord, User, StudentCourseEnrollment, AttendanceStatus
import cv2

_active_session_cache = {"session": None, "timestamp": None, "ttl": 300}  


def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance in meters between two points"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371000  
    return c * r


def _get_active_session(session):
    """Get active session with caching to reduce DB calls (returns dict, not ORM object)"""
    current_time = datetime.now()

    if (
        _active_session_cache["session"]
        and _active_session_cache["timestamp"]
        and (current_time - _active_session_cache["timestamp"]).seconds < _active_session_cache["ttl"]
    ):
        return _active_session_cache["session"]

    attendance_session = (
        session.query(AttendanceSession)
        .options(joinedload(AttendanceSession.course))
        .filter(AttendanceSession.is_active)
        .filter(
            or_(
                AttendanceSession.end_time.is_(None),
                AttendanceSession.end_time > current_time,
            )
        )
        .order_by(AttendanceSession.start_time.desc())
        .first()
    )

    session_data = None
    if attendance_session:
        session_data = {
            "id": attendance_session.id,
            "course_id": attendance_session.course_id,
            "lat": attendance_session.lat,
            "long": attendance_session.long,
            "radius_meters": attendance_session.radius_meters,
            "start_time": attendance_session.start_time,
            "end_time": attendance_session.end_time,
        }

    _active_session_cache["session"] = session_data
    _active_session_cache["timestamp"] = current_time

    return session_data


def _preprocess_image_fast(face_image_bytes: bytes):
    
    try:
        nparr = np.frombuffer(face_image_bytes, np.uint8)
        image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image_bgr is None:
            return None, "Invalid image format"

        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        height, width = image_rgb.shape[:2]
        if width > 1024 or height > 1024:
            if width > height:
                new_width = 1024
                new_height = int((height * 1024) / width)
            else:
                new_height = 1024
                new_width = int((width * 1024) / height)
            image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return image_rgb, None

    except Exception as e:
        return None, f"Image preprocessing error: {str(e)}"


def register_attendance(
    student_id: str, face_image_bytes: bytes, student_latitude: float, student_longitude: float
) -> tuple[bool, str]:
    with Database.get_session() as session:
        try:
            current_time = datetime.now()

            attendance_session = _get_active_session(session)
            if not attendance_session:
                return False, "No active attendance session found"

            query_result = (
                session.query(User, StudentCourseEnrollment, AttendanceRecord)
                .outerjoin(
                    StudentCourseEnrollment,
                    (StudentCourseEnrollment.student_id == User.reg_no)
                    & (StudentCourseEnrollment.course_id == attendance_session["course_id"]),
                )
                .outerjoin(
                    AttendanceRecord,
                    (AttendanceRecord.student_id == User.reg_no)
                    & (AttendanceRecord.session_id == attendance_session["id"]),
                )
                .filter(User.reg_no == student_id)
                .first()
            )

            if not query_result or not query_result[0]:
                return False, "Student not found"

            student, enrollment, existing_record = query_result

            if not enrollment:
                return False, "Student is not enrolled in this course"

            if existing_record:
                return False, "Attendance already recorded for this session"

            distance = haversine(
                student_longitude,
                student_latitude,
                attendance_session["long"],
                attendance_session["lat"],
            )
            if distance > attendance_session["radius_meters"]:
                return (
                    False,
                    f"Location verification failed. You are {distance:.1f}m away (max allowed: {attendance_session['radius_meters']}m)",
                )

            image_rgb, error = _preprocess_image_fast(face_image_bytes)
            if error:
                return False, error

            face_locations = face_recognition.face_locations(image_rgb, model="hog")
            if len(face_locations) == 0:
                return False, "No face detected in the uploaded image"
            if len(face_locations) > 1:
                return False, "Multiple faces detected. Please upload image with single face"

            face_encodings = face_recognition.face_encodings(image_rgb, face_locations, model="small")
            if len(face_encodings) == 0:
                return False, "Failed to extract face features"

            uploaded_face_encoding = face_encodings[0]
            stored_face_encoding = np.array(student.face)

            face_distance = np.linalg.norm(stored_face_encoding - uploaded_face_encoding)
            face_match = face_distance <= 0.6
            if not face_match:
                return False, f"Face verification failed. Distance: {face_distance:.3f}"

            attendance_record = AttendanceRecord(
                session_id=attendance_session["id"],
                student_id=student_id,
                status=AttendanceStatus.present,
                timestamp=current_time,
                student_latitude=student_latitude,
                student_longitude=student_longitude,
            )
            session.add(attendance_record)
            session.commit()

            return True, "Attendance registered successfully"

        except IntegrityError:
            session.rollback()
            return False, "Attendance may already be recorded"
        except Exception as e:
            session.rollback()
            return False, f"Unexpected error: {str(e)}"


def clear_session_cache():
    """Clear the active session cache - call this when sessions are updated"""
    global _active_session_cache
    _active_session_cache["session"] = None
    _active_session_cache["timestamp"] = None
