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


def enroll_students_to_course(course_id: int, student_reg_nos: List[str]) -> bool:
    """
    Enroll multiple students to a course.
    """
    try:
        with Database.get_session() as session:
            course = session.query(Course).filter_by(id=course_id).first()
            if not course:
                print(f"Error: Course with ID {course_id} not found")
                return False

            enrolled_count = 0
            for reg_no in student_reg_nos:
                student = session.query(User).filter_by(
                    reg_no=reg_no,
                    role=UserRole.student
                ).first()

                if not student:
                    print(f"Warning: Student with reg_no '{reg_no}' not found")
                    continue

            
                existing_enrollment = session.query(StudentCourseEnrollment).filter_by(
                    student_id=reg_no,
                    course_id=course_id
                ).first()

                if existing_enrollment:
                    print(f"Warning: Student '{reg_no}' already enrolled in course '{course.course_code}'")
                    continue

                enrollment = StudentCourseEnrollment(
                    student_id=reg_no,
                    course_id=course_id
                )
                session.add(enrollment)
                enrolled_count += 1

            session.commit()
            print(f"Successfully enrolled {enrolled_count} students to course '{course.course_code}'")
            return True
    except Exception as e:
        print(f"Error enrolling students: {str(e)}")
        return False

def assign_faculty_to_course(course_id: int, faculty_reg_nos: List[str]) -> bool:
    """
    Assign multiple faculty members to a course.
    """
    try:
        with Database.get_session() as session:
            course = session.query(Course).filter_by(id=course_id).first()
            if not course:
                print(f"Error: Course with ID {course_id} not found")
                return False

            assigned_count = 0
            for reg_no in faculty_reg_nos:
                faculty = session.query(User).filter_by(
                    reg_no=reg_no,
                    role=UserRole.faculty
                ).first()

                if not faculty:
                    print(f"Warning: Faculty with reg_no '{reg_no}' not found")
                    continue

                if faculty in course.assigned_faculty:
                    print(f"Warning: Faculty '{reg_no}' already assigned to course '{course.course_code}'")
                    continue

                course.assigned_faculty.append(faculty)
                assigned_count += 1

            session.commit()
            print(f"Successfully assigned {assigned_count} faculty members to course '{course.course_code}'")
            return True
    except Exception as e:
        print(f"Error assigning faculty: {str(e)}")
        return False
