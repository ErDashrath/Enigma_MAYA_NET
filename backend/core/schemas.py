"""
Pydantic schemas for Django Ninja API
"""
from ninja import Schema
from typing import Optional


class LoginSchema(Schema):
    username: str
    password: str


class RegisterSchema(Schema):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserSchema(Schema):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    date_joined: str


class TokenSchema(Schema):
    access_token: str
    token_type: str = "bearer"
    user: UserSchema


class MessageSchema(Schema):
    message: str


class ErrorSchema(Schema):
    error: str
    detail: Optional[str] = None


# VitalCircle specific schemas
class VitalSignsSchema(Schema):
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    stress_level: Optional[int] = None  # 1-10 scale
    sodium_intake: Optional[float] = None  # mg
    recorded_at: Optional[str] = None


class StabilityScoreSchema(Schema):
    score: float  # 0-100 percentage
    risk_level: str  # "low", "medium", "high"
    recommendations: list[str]
    last_updated: str