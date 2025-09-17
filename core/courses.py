from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import or_
from models import (Course, User, StudentCourseEnrollment, UserRole, Classroom, TimeSlot,
                    ClassSchedule, DayOfWeek, ClassType,faculty_course_assignment)
from typing import List, Optional
from utils.db import Database  


def create_course(course_name: str, course_code: str,credits: int,department: str) -> Optional[Course]:
    """
    Create a new course.
    """
    try:
        with Database.get_session() as session:
            course = Course(
                course_name=course_name,
                course_code=course_code,
                credits = credits
            )
            session.add(course)
            session.commit()
            session.refresh(course)  
            print(f"Course '{course_name}' created successfully with ID: {course.id}")
            return course
    except IntegrityError:
        print(f"Error: Course with code '{course_code}' already exists")
        return None
    except Exception as e:
        print(f"Error creating course: {str(e)}")
        return None
