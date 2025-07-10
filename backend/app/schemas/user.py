"""
User and Authentication Schemas

This module contains Pydantic schemas for user management and authentication.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# Simple email validation function
def validate_email(email: str) -> str:
    """Simple email validation without external dependencies"""
    if '@' not in email or '.' not in email.split('@')[1]:
        raise ValueError('Invalid email format')
    return email
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: str = Field(..., description="Valid email address")

    @validator('email')
    def validate_email_format(cls, v):
        return validate_email(v)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100, description="Password (8-100 characters)")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = None
    is_active: Optional[bool] = None

    @validator('email')
    def validate_email_format(cls, v):
        if v is not None:
            return validate_email(v)
        return v


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user schema (without sensitive data)"""
    pass


class UserWithAlerts(User):
    """User schema with alerts included"""
    alerts: List['AlertResponse'] = []


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    user: User
    token: Token


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# Alert schemas (will be imported by alert schemas)
class AlertBase(BaseModel):
    make: Optional[str] = Field(None, max_length=50, description="Car manufacturer")
    model: Optional[str] = Field(None, max_length=100, description="Car model")
    min_price: Optional[int] = Field(None, ge=0, description="Minimum price in EUR")
    max_price: Optional[int] = Field(None, ge=0, description="Maximum price in EUR")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Car year")
    fuel_type: Optional[str] = Field(None, max_length=20, description="Fuel type")
    transmission: Optional[str] = Field(None, max_length=20, description="Transmission type")
    city: Optional[str] = Field(None, max_length=100, description="City location")


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    make: Optional[str] = Field(None, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    fuel_type: Optional[str] = Field(None, max_length=20)
    transmission: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Forward reference resolution
UserWithAlerts.model_rebuild()
