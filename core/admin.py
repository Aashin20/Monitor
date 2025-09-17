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


def create_time_slot(name: str, start_time: str, end_time: str) -> bool:
    with Database.get_session() as session:
        existing_slot = session.query(TimeSlot).filter_by(name=name).first()
        if existing_slot:
            return False
        
        start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        
        time_slot = TimeSlot(
            name=name,
            start_time=start_time_obj,
            end_time=end_time_obj
        )
        session.add(time_slot)
        session.commit()
        return True