"""
Authentication Service for Phase 5.1
JWT-based authentication with user management
"""

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import UUID
import asyncpg
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from pydantic import ValidationError

from api.models.auth import UserInDB, TokenData, UserProfileResponse
from api.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service handling JWT tokens and user management"""
    
    def __init__(self):
        # JWT Configuration
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Database service
        self.db_service = DatabaseService()
        
        # Cache for revoked tokens (in production, use Redis)
        self.revoked_tokens = set()
        
        logger.info("🔐 Authentication service initialized")
    
    # =====================================================================================
    # Password Management
    # =====================================================================================
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # =====================================================================================
    # JWT Token Management
    # =====================================================================================
    
    def create_access_token(self, user: UserInDB, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        # Create token payload
        payload = {
            "sub": user.email,
            "user_id": str(user.id),
            "username": user.username,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16)  # JWT ID for token revocation
        }
        
        # Create and return token
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔐 Created access token for user {user.email}")
        return token
    
    def create_refresh_token(self, user: UserInDB) -> str:
        """Create JWT refresh token"""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user.email,
            "user_id": str(user.id),
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_urlsafe(16)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔐 Created refresh token for user {user.email}")
        return token
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and validate JWT token"""
        try:
            # Check if token is revoked
            if token in self.revoked_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Extract token data
            email: str = payload.get("sub")
            user_id_str: str = payload.get("user_id")
            username: str = payload.get("username")
            
            if email is None or user_id_str is None or username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Parse user_id as UUID
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID in token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Create token data
            token_data = TokenData(
                sub=email,
                user_id=user_id,
                username=username,
                exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc),
                iat=datetime.fromtimestamp(payload.get("iat"), tz=timezone.utc),
                jti=payload.get("jti")
            )
            
            return token_data
            
        except JWTError as e:
            logger.warning(f"🚫 JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except ValidationError as e:
            logger.warning(f"🚫 Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def revoke_token(self, token: str) -> None:
        """Revoke a JWT token"""
        # In production, this should use Redis with expiration
        self.revoked_tokens.add(token)
        logger.info("🚫 Token revoked")
    
    # =====================================================================================
    # User Management
    # =====================================================================================
    
    async def create_user(self, email: str, username: str, password: str) -> UserInDB:
        """Create a new user account"""
        try:
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Insert user into database
            query = """
                INSERT INTO users (email, username, hashed_password, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                RETURNING id, email, username, hashed_password, is_active, created_at, updated_at
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, email, username, hashed_password, True)
                
                if not row:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create user account"
                    )
                
                user = UserInDB(**dict(row))
                logger.info(f"✅ Created user account: {email}")
                return user
                
        except asyncpg.UniqueViolationError as e:
            if "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address is already registered"
                )
            elif "username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already taken"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User account already exists"
                )
        except Exception as e:
            logger.error(f"❌ Error creating user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user account"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email address"""
        try:
            query = """
                SELECT id, email, username, hashed_password, is_active, created_at, updated_at
                FROM users 
                WHERE email = $1 AND is_active = TRUE
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, email)
                
                if row:
                    return UserInDB(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching user by email: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            query = """
                SELECT id, email, username, hashed_password, is_active, created_at, updated_at
                FROM users 
                WHERE id = $1 AND is_active = TRUE
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, user_id)
                
                if row:
                    return UserInDB(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"❌ Error fetching user by ID: {str(e)}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user credentials"""
        user = await self.get_user_by_email(email)
        
        if not user:
            logger.warning(f"🚫 Authentication failed: user not found - {email}")
            return None
        
        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"🚫 Authentication failed: invalid password - {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"🚫 Authentication failed: account inactive - {email}")
            return None
        
        logger.info(f"✅ User authenticated successfully: {email}")
        return user
    
    async def update_user_profile(self, user_id: UUID, updates: Dict[str, Any]) -> Optional[UserInDB]:
        """Update user profile information"""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            param_idx = 1
            
            for field, value in updates.items():
                if field in ['username', 'email']:  # Only allow specific fields
                    set_clauses.append(f"{field} = ${param_idx}")
                    params.append(value)
                    param_idx += 1
            
            if not set_clauses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid fields to update"
                )
            
            # Add updated_at and user_id parameters
            set_clauses.append(f"updated_at = ${param_idx}")
            params.append(datetime.now(timezone.utc))
            param_idx += 1
            
            params.append(user_id)  # For WHERE clause
            
            query = f"""
                UPDATE users 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_idx} AND is_active = TRUE
                RETURNING id, email, username, hashed_password, is_active, created_at, updated_at
            """
            
            async with self.db_service.get_connection() as conn:
                row = await conn.fetchrow(query, *params)
                
                if row:
                    user = UserInDB(**dict(row))
                    logger.info(f"✅ Updated user profile: {user.email}")
                    return user
                return None
                
        except asyncpg.UniqueViolationError as e:
            if "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address is already taken"
                )
            elif "username" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already taken"
                )
        except Exception as e:
            logger.error(f"❌ Error updating user profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
    
    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            # Get current user
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify current password
            if not self.verify_password(current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
            
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update password in database
            query = """
                UPDATE users 
                SET hashed_password = $1, updated_at = NOW()
                WHERE id = $2 AND is_active = TRUE
            """
            
            async with self.db_service.get_connection() as conn:
                result = await conn.execute(query, hashed_password, user_id)
                
                if result == "UPDATE 1":
                    logger.info(f"✅ Password changed for user: {user.email}")
                    return True
                return False
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error changing password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    # =====================================================================================
    # Password Reset (Simplified - for production, use email service)
    # =====================================================================================
    
    async def generate_password_reset_token(self, email: str) -> Optional[str]:
        """Generate password reset token (simplified implementation)"""
        user = await self.get_user_by_email(email)
        if not user:
            return None  # Don't reveal if email exists
        
        # Create reset token (expires in 1 hour)
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
        payload = {
            "sub": user.email,
            "user_id": str(user.id),
            "type": "password_reset",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"🔐 Generated password reset token for: {email}")
        
        # In production, send email with reset link
        logger.info(f"📧 Password reset link: /reset-password?token={token}")
        
        return token
    
    async def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            user_id = UUID(payload.get("user_id"))
            user = await self.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Hash new password and update
            hashed_password = self.hash_password(new_password)
            
            query = """
                UPDATE users 
                SET hashed_password = $1, updated_at = NOW()
                WHERE id = $2 AND is_active = TRUE
            """
            
            async with self.db_service.get_connection() as conn:
                result = await conn.execute(query, hashed_password, user_id)
                
                if result == "UPDATE 1":
                    logger.info(f"✅ Password reset completed for: {user.email}")
                    return True
                return False
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        except Exception as e:
            logger.error(f"❌ Error resetting password: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset password"
            )

# Global auth service instance
auth_service = AuthService()