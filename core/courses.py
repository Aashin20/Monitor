from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
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


def get_course_info(course_id: int) -> Optional[dict]:

    with Database.get_session() as session:
        course = (
            session.query(Course)
            .options(
                selectinload(Course.enrollments).joinedload(StudentCourseEnrollment.student),
                selectinload(Course.assigned_faculty)
            )
            .filter_by(id=course_id)
            .first()
        )

        if not course:
            return None

        enrolled_students = [
            {
                'reg_no': enrollment.student.reg_no,
                'name': enrollment.student.name,
                'enrolled_at': enrollment.enrolled_at
            }
            for enrollment in course.enrollments
        ]

        assigned_faculty = [
            {
                'reg_no': faculty.reg_no,
                'name': faculty.name
            }
            for faculty in course.assigned_faculty
        ]

        return {
            'course_id': course.id,
            'course_name': course.course_name,
            'course_code': course.course_code,
            'enrolled_students': enrolled_students,
            'assigned_faculty': assigned_faculty,
            'total_students': len(enrolled_students),
            'total_faculty': len(assigned_faculty)
        }


def create_class_schedule(
    course_code: str,
    faculty_reg_no: str,
    classroom_number: str,
    time_slot_name: str,
    day_of_week: DayOfWeek,
    class_type: ClassType,
    section: Optional[str] = None,
    notes: Optional[str] = None
) -> ClassSchedule:
   
    with Database.get_session() as session:
        course = session.query(Course).filter(Course.course_code == course_code).one_or_none()
        if not course:
            raise ValueError(f"Course with code '{course_code}' not found.")

        faculty = session.query(User).filter(User.reg_no == faculty_reg_no).one_or_none()
        if not faculty:
            raise ValueError(f"User with registration number '{faculty_reg_no}' not found.")
        if faculty.role != UserRole.faculty:  
            raise ValueError(f"User '{faculty.name}' is not a faculty member.")

        assignment_check = session.query(faculty_course_assignment).filter_by(
            faculty_id=faculty.reg_no, course_id=course.id
        ).first()
        if not assignment_check:
            raise ValueError(
                f"Faculty '{faculty.name}' is not formally assigned to teach course '{course.course_name}'."
            )

        classroom = session.query(Classroom).filter(Classroom.class_number == classroom_number).one_or_none()
        if not classroom:
            raise ValueError(f"Classroom '{classroom_number}' not found.")

        time_slot = session.query(TimeSlot).filter(TimeSlot.name == time_slot_name).one_or_none()
        if not time_slot:
            raise ValueError(f"Time slot '{time_slot_name}' not found.")

        conflict = session.query(ClassSchedule).filter(
                        ClassSchedule.day_of_week == day_of_week,
                        ClassSchedule.time_slot_id == time_slot.id
                    ).filter(
                        (ClassSchedule.faculty_id == faculty.reg_no) |
                        (ClassSchedule.classroom_id == classroom.id)
                    ).first()


        if conflict:
            if conflict.faculty_id == faculty.reg_no:
                raise ValueError(
                    f"Conflict: Faculty '{faculty.name}' is already scheduled for another class at this time."
                )
            if conflict.classroom_id == classroom.id:
                raise ValueError(
                    f"Conflict: Classroom '{classroom.class_number}' is already booked at this time."
                )

        new_schedule = ClassSchedule(
            course_id=course.id,
            faculty_id=faculty.reg_no,  
            classroom_id=classroom.id,
            time_slot_id=time_slot.id,
            day_of_week=day_of_week,
            class_type=class_type,
            section=section,
            notes=notes
        )
        session.add(new_schedule)
        session.flush()
        session.commit()
        session.refresh(new_schedule)
        return new_schedule
