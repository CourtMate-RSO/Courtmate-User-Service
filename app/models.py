from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    id_token: str
    email: EmailStr
    name: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    role: str | None = None
    first_login: bool | None = None