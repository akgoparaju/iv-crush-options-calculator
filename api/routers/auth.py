"""
Authentication Router for Phase 5.1
JWT-based authentication endpoints
"""

import logging
from datetime import timedelta
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

from api.models.auth import (
    UserRegisterRequest, UserLoginRequest, UserUpdateRequest,
    PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest,
    AuthResponse, TokenResponse, UserProfileResponse, PasswordResetResponse,
    TokenData, UserInDB
)
from api.services.auth_service import auth_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer security scheme
security = HTTPBearer()

# =====================================================================================
# Authentication Dependencies
# =====================================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get current authenticated user from JWT token"""
    try:
        # Extract token
        token = credentials.credentials
        
        # Decode token
        token_data = auth_service.decode_token(token)
        
        # Get user from database
        user = await auth_service.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user (alias for get_current_user for clarity)"""
    return current_user

# =====================================================================================
# Authentication Endpoints
# =====================================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterRequest, background_tasks: BackgroundTasks):
    """
    Register a new user account
    
    Creates a new user with email verification (placeholder for now)
    """
    try:
        # Create user account
        user = await auth_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password
        )
        
        # Convert to response format
        user_profile = UserProfileResponse.from_orm(user)
        
        # Create tokens
        access_token = auth_service.create_access_token(user)
        refresh_token = auth_service.create_refresh_token(user)
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            user=user_profile
        )
        
        # Add background task for welcome email (placeholder)
        background_tasks.add_task(
            _send_welcome_email_placeholder,
            user.email,
            user.username
        )
        
        return AuthResponse(
            success=True,
            message="Account created successfully",
            user=user_profile,
            token=token_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

@router.post("/login", response_model=AuthResponse)
async def login_user(login_data: UserLoginRequest):
    """
    Authenticate user and return JWT tokens
    
    Returns access token and refresh token for successful authentication
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Convert to response format
        user_profile = UserProfileResponse.from_orm(user)
        
        # Create tokens
        access_token = auth_service.create_access_token(user)
        refresh_token = auth_service.create_refresh_token(user)
        
        token_response = TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            refresh_token=refresh_token,
            user=user_profile
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            user=user_profile,
            token=token_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Logout user and revoke access token
    
    Adds token to revocation list to prevent further use
    """
    try:
        # Revoke token
        token = credentials.credentials
        auth_service.revoke_token(token)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Logout successful"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Refresh access token using refresh token
    
    Validates refresh token and issues new access token
    """
    try:
        # Extract and decode refresh token
        refresh_token = credentials.credentials
        token_data = auth_service.decode_token(refresh_token)
        
        # Get user
        user = await auth_service.get_user_by_id(token_data.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        access_token = auth_service.create_access_token(user)
        user_profile = UserProfileResponse.from_orm(user)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            refresh_token=refresh_token,  # Return same refresh token
            user=user_profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# =====================================================================================
# User Profile Management
# =====================================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: UserInDB = Depends(get_current_user)):
    """
    Get current user profile information
    
    Returns user profile data for authenticated user
    """
    return UserProfileResponse.from_orm(current_user)

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Update user profile information
    
    Updates username and/or email for authenticated user
    """
    try:
        # Prepare updates
        updates = {}
        if update_data.username is not None:
            updates['username'] = update_data.username
        if update_data.email is not None:
            updates['email'] = update_data.email
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        # Update user
        updated_user = await auth_service.update_user_profile(current_user.id, updates)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfileResponse.from_orm(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

# =====================================================================================
# Password Management
# =====================================================================================

@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Change user password
    
    Changes password for authenticated user after verifying current password
    """
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Password changed successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(reset_data: PasswordResetRequest, background_tasks: BackgroundTasks):
    """
    Request password reset
    
    Generates password reset token and sends reset email (placeholder)
    """
    try:
        # Generate reset token
        token = await auth_service.generate_password_reset_token(reset_data.email)
        
        # Always return success to prevent email enumeration
        success_response = PasswordResetResponse(
            success=True,
            message="If the email exists, a password reset link has been sent",
            email=reset_data.email
        )
        
        # If token was generated, add background task to send email
        if token:
            background_tasks.add_task(
                _send_password_reset_email_placeholder,
                reset_data.email,
                token
            )
        
        return success_response
        
    except Exception as e:
        logger.error(f"❌ Password reset request error: {str(e)}")
        # Still return success to prevent information disclosure
        return PasswordResetResponse(
            success=True,
            message="If the email exists, a password reset link has been sent",
            email=reset_data.email
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Reset password using reset token
    
    Validates reset token and updates user password
    """
    try:
        success = await auth_service.reset_password_with_token(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Password reset successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

# =====================================================================================
# Account Management
# =====================================================================================

@router.delete("/account")
async def delete_account(
    current_user: UserInDB = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Deactivate user account
    
    Soft delete - marks account as inactive rather than deleting data
    """
    try:
        # Mark account as inactive
        updates = {"is_active": False}
        await auth_service.update_user_profile(current_user.id, updates)
        
        # Revoke current token
        token = credentials.credentials
        auth_service.revoke_token(token)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": "Account deactivated successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Account deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )

# =====================================================================================
# Admin Endpoints (for future expansion)
# =====================================================================================

@router.get("/admin/users")
async def list_users(
    current_user: UserInDB = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """
    List all users (admin only - placeholder)
    
    Future: Add admin role checking
    """
    # Placeholder for admin functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin functionality not yet implemented"
    )

# =====================================================================================
# Helper Functions (Background Tasks)
# =====================================================================================

async def _send_welcome_email_placeholder(email: str, username: str):
    """Placeholder for welcome email sending"""
    logger.info(f"📧 Welcome email would be sent to {email} (username: {username})")
    # In production: integrate with email service (SendGrid, AWS SES, etc.)

async def _send_password_reset_email_placeholder(email: str, token: str):
    """Placeholder for password reset email sending"""
    logger.info(f"📧 Password reset email would be sent to {email} with token: {token}")
    # In production: integrate with email service