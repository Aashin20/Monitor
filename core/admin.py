from models import (Classroom, TimeSlot)
from utils.db import Database  
from datetime import datetime

def create_classroom(class_number: str) -> Classroom:
    with Database.get_session() as session:
        existing_classroom = session.query(Classroom).filter_by(class_number=class_number).first()
        if existing_classroom:
            return False
        classroom = Classroom(class_number=class_number)
        session.add(classroom)
        session.commit()
        return True
