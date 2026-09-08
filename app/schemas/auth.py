from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class OfficerCreate(BaseModel):
    name: str
    email: str
    password: str
    department_id: int