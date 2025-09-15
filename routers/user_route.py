from fastapi import APIRouter
from core.auth import register, Register,login

router = APIRouter()

@router.post("/register")
async def reg_user(details: Register):
    return register(details)

@router.get("/login")
async def login_user(reg_no: str, password: str):
    return login(reg_no, password)