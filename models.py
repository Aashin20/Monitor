import enum
from sqlalchemy import (Column,Integer,String,Float,DateTime,
    ForeignKey,Enum,LargeBinary,Text,Table,ARRAY,func,Boolean)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class UserRole(enum.Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"

class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

class LeaveStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"



faculty_course_assignment = Table('faculty_course_assignments', Base.metadata,
    Column('faculty_id', Integer, ForeignKey('users.reg_no'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)


class User(Base):
    
    __tablename__ = 'users'
    reg_no = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    pfp = Column(LargeBinary, nullable=True)
    face = Column(ARRAY(Float), nullable=False)


    courses_assigned = relationship(
        "Course",
        secondary=faculty_course_assignment,
        back_populates="assigned_faculty"
    )

  
    enrollments = relationship("StudentCourseEnrollment", back_populates="student")
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    leave_requests = relationship("LeaveRequest", back_populates="student")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.full_name}', role='{self.role.value}')>"


class Course(Base):
  
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    course_name = Column(String(100), nullable=False)
    course_code = Column(String(20), unique=True, nullable=False)


    assigned_faculty = relationship(
        "User",
        secondary=faculty_course_assignment,
        back_populates="courses_assigned"
    )

  
    enrollments = relationship("StudentCourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    attendance_sessions = relationship("AttendanceSession", back_populates="course", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.course_name}')>"


class StudentCourseEnrollment(Base):
  
    __tablename__ = 'student_course_enrollments'
    student_id = Column(Integer, ForeignKey('users.reg_no'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class AttendanceSession(Base):
    
    __tablename__ = 'attendance_sessions'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    faculty_id = Column(Integer, ForeignKey('users.reg_no'), nullable=False)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime, nullable=True)
    lat = Column(Float, nullable=False)
    long = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, server_default="true", nullable=False)
    remarks = Column(Text, nullable=True)

    course = relationship("Course", back_populates="attendance_sessions")
    created_by_faculty = relationship("User", foreign_keys=[faculty_id])
    records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")



class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = Column(Integer, ForeignKey('users.reg_no'), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    student_latitude = Column(Float, nullable=True)
    student_longitude = Column(Float, nullable=True)

    session = relationship("AttendanceSession", back_populates="records")
    student = relationship("User", back_populates="attendance_records")

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.reg_no'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    attachment_url = Column(String(255), nullable=True)
    reviewed_by_faculty_id = Column(Integer, ForeignKey('users.reg_no'), nullable=True)
    faculty_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User", back_populates="leave_requests")
    faculty_reviewer = relationship("User", foreign_keys=[reviewed_by_faculty_id])