from utils.db import Database
from pydantic import BaseModel,Base64Bytes
from models import User,UserRole
import bcrypt
import io
import face_recognition
from PIL import UnidentifiedImageError

class Register(BaseModel):
    reg_no: str
    name: str
    password: str
    parent_email: str
    role: UserRole
    pfp: Base64Bytes = None
    face: Base64Bytes

def register(details: Register):
    with Database.get_session() as session:
        if session.query(User).filter(User.reg_no == details.reg_no).first():
            return False, "A user with this registration number already exists."
    try:
        image_stream = io.BytesIO(details.face)
        image = face_recognition.load_image_file(image_stream)
        face_encodings = face_recognition.face_encodings(image)
    except UnidentifiedImageError:
        return False, "Invalid image format. Please upload a valid PNG or JPG file."
    except Exception as e:
        return False, f"An unexpected error occurred while processing the image: {e}"

    if not face_encodings:
        return False, "No face could be detected in the image. Please use a clearer picture."

    if len(face_encodings) > 1:
        return False, "Multiple faces were detected. Please upload a picture with only one person."

    user_face_encoding = face_encodings[0]

    with Database.get_session() as session:
        hashed_password = bcrypt.hashpw(details.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(
            reg_no=details.reg_no,
            name=details.name,
            password_hash=hashed_password,
            parent_email=details.parent_email,
            role=details.role,
            pfp=details.pfp,
            face=user_face_encoding.tolist()
        )
        
        session.add(new_user)
        session.commit()
        return True, "User registered successfully."
    


