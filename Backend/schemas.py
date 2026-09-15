"""Pydantic models — used only for auth endpoints where validation matters."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal


class RegisterIn(BaseModel):
    role: Literal["patient", "doctor"]
    firstName: str = Field(min_length=1, max_length=40)
    lastName: str = Field(min_length=1, max_length=40)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = ""
    blood: Optional[str] = ""
    dept: Optional[str] = None
    ayush: Optional[bool] = False
    aadhaarLast4: Optional[str] = None
    degreeFileName: Optional[str] = None
    degreeFileType: Optional[str] = None
    degreeFileSize: Optional[int] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    role: Literal["patient", "doctor"]


class TokenOut(BaseModel):
    token: str
    user: dict