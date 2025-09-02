"""
Authentication Models for Phase 5.1
JWT-based authentication with user management
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from uuid import UUID
import re

# =====================================================================================
# Request Models
# =====================================================================================

class UserRegisterRequest(BaseModel):
    """User registration request model"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate that passwords match"""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")

class UserUpdateRequest(BaseModel):
    """User profile update request model"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format if provided"""
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        return v
    
    @validator('confirm_password')
    def validate_password_match(cls, v, values):
        """Validate that passwords match"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# =====================================================================================
# Response Models
# =====================================================================================

class UserProfileResponse(BaseModel):
    """User profile response model"""
    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: str = Field(..., description="Username")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last profile update")
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """JWT token response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    user: UserProfileResponse = Field(..., description="User profile information")

class AuthResponse(BaseModel):
    """Authentication response model"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    user: Optional[UserProfileResponse] = Field(None, description="User profile")
    token: Optional[TokenResponse] = Field(None, description="Authentication token")

class PasswordResetResponse(BaseModel):
    """Password reset response model"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    email: Optional[str] = Field(None, description="Email address (if successful)")

# =====================================================================================
# Internal Models
# =====================================================================================

class TokenData(BaseModel):
    """Token payload data model"""
    sub: str = Field(..., description="Subject (user email)")
    user_id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    jti: Optional[str] = Field(None, description="JWT ID")

class UserInDB(BaseModel):
    """User database model"""
    id: UUID
    email: str
    username: str
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# =====================================================================================
# OAuth Models (for future expansion)
# =====================================================================================

class OAuthProvider(BaseModel):
    """OAuth provider configuration model"""
    provider: str = Field(..., description="OAuth provider name (google, github)")
    client_id: str = Field(..., description="OAuth client ID")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    scopes: List[str] = Field(default=[], description="OAuth scopes")

class OAuthTokenRequest(BaseModel):
    """OAuth token exchange request"""
    provider: str = Field(..., description="OAuth provider")
    code: str = Field(..., description="Authorization code")
    state: Optional[str] = Field(None, description="State parameter")