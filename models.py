import enum
from sqlalchemy import (Column,Integer,String,Float,DateTime,
    ForeignKey,Enum,LargeBinary,Text,Table,func,Boolean,Time,Float)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSON

Base = declarative_base()


class UserRole(enum.Enum):
    student = "student"
    faculty = "faculty"
    admin = "admin"

class AttendanceStatus(enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"

class LeaveStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class DayOfWeek(enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class ClassType(enum.Enum):
    lecture = "lecture"
    lab = "lab"
    tutorial = "tutorial"
    seminar = "seminar"



faculty_course_assignment = Table('faculty_course_assignments', Base.metadata,
    Column('faculty_id', String, ForeignKey('users.reg_no'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    reg_no = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole),nullable=False)
    pfp = Column(LargeBinary, nullable=True)
    face = Column(JSON, nullable=False)

    courses_assigned = relationship(
        "Course",
        secondary=faculty_course_assignment,
        back_populates="assigned_faculty"
    )
    enrollments = relationship("StudentCourseEnrollment", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    leave_requests = relationship(
        "LeaveRequest",
        foreign_keys="LeaveRequest.student_id",
        back_populates="student"
    )
    reviewed_leave_requests = relationship(
        "LeaveRequest",
        foreign_keys="LeaveRequest.reviewed_by_faculty_id",
        back_populates="faculty_reviewer"
    )

    teaching_schedules = relationship(
        "ClassSchedule",
        foreign_keys="ClassSchedule.faculty_id",
        back_populates="faculty"
    )
    def __repr__(self):
        return f"<User(reg_no={self.reg_no}, name='{self.name}', role='{self.role.value}')>"


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    course_name = Column(String(100), nullable=False)
    course_code = Column(String(20), unique=True, nullable=False)
    credits = Column(Integer, nullable=False, default=3) 
    department = Column(String(50), nullable=True)

    assigned_faculty = relationship(
        "User",
        secondary=faculty_course_assignment,
        back_populates="courses_assigned"
    )
    enrollments = relationship("StudentCourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="course", cascade="all, delete-orphan")
    

    schedules = relationship("ClassSchedule", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.course_name}')>"


class StudentCourseEnrollment(Base):
    __tablename__ = 'student_course_enrollments'
    student_id = Column(String, ForeignKey('users.reg_no'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class Classroom(Base):
    """Represents classrooms/venues"""
    __tablename__ = 'classrooms'
    
    id = Column(Integer, primary_key=True)
    class_number = Column(String(20), unique=True, nullable=False)  
    
   
    schedules = relationship("ClassSchedule", back_populates="classroom")
    
    def __repr__(self):
        return f"<Classroom(id={self.id}, number='{self.class_number}')>"


class TimeSlot(Base):
    """Represents time periods (e.g., 9:00-10:30 AM)"""
    __tablename__ = 'time_slots'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False) 
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    schedules = relationship("ClassSchedule", back_populates="time_slot")
    
    def __repr__(self):
        return f"<TimeSlot(id={self.id}, name='{self.name}', {self.start_time}-{self.end_time})>"


class ClassSchedule(Base):
    """Main timetable table - represents scheduled classes"""
    __tablename__ = 'class_schedules'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    faculty_id = Column(String, ForeignKey('users.reg_no'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=False)
    time_slot_id = Column(Integer, ForeignKey('time_slots.id'), nullable=False)
    
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    class_type = Column(Enum(ClassType), default=ClassType.lecture, nullable=False)
    

    section = Column(String(10), nullable=True)  
    max_students = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    

    course = relationship("Course", back_populates="schedules")
    faculty = relationship("User", foreign_keys=[faculty_id], back_populates="teaching_schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    time_slot = relationship("TimeSlot", back_populates="schedules")
    
    def __repr__(self):
        return f"<ClassSchedule(id={self.id}, course={self.course.course_code if self.course else 'None'}, day={self.day_of_week.value})>"



class AttendanceSession(Base):
    __tablename__ = 'attendance_sessions'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    faculty_id = Column(String, ForeignKey('users.reg_no'), nullable=False)  
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    lat = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    remarks = Column(Text, nullable=True)

    schedule_id = Column(Integer, ForeignKey('class_schedules.id'), nullable=True)

    course = relationship("Course", back_populates="attendance_sessions")
    created_by_faculty = relationship("User", foreign_keys=[faculty_id])
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = Column(String, ForeignKey('users.reg_no'), nullable=False)  
    status = Column(Enum(AttendanceStatus), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    student_latitude = Column(Float, nullable=True)
    student_longitude = Column(Float, nullable=True)

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("User", back_populates="attendance_records")


class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey('users.reg_no'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.pending, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    reviewed_by_faculty_id = Column(String, ForeignKey('users.reg_no'), nullable=True)
    faculty_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", foreign_keys=[student_id], back_populates="leave_requests")
    faculty_reviewer = relationship("User", foreign_keys=[reviewed_by_faculty_id], back_populates="reviewed_leave_requests")
