"""
Authentication and Authorization Module

Provides JWT-based authentication and role-based access control (RBAC)
for the Finance Analytics & Trading Co-Pilot API.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings

# JWT Configuration
SECRET_KEY = settings.JWT_SECRET_KEY if hasattr(settings, 'JWT_SECRET_KEY') else "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Pydantic Models
class Token(BaseModel):
    """Access token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    roles: List[str] = []


class User(BaseModel):
    """User model"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = []


class UserInDB(User):
    """User model with hashed password"""
    hashed_password: str


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    roles: List[str] = ["user"]  # Default role


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


# Role definitions
class Role:
    """Role constants for RBAC"""
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    USER = "user"
    READONLY = "readonly"


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        roles: List[str] = payload.get("roles", [])

        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(username=username, user_id=user_id, roles=roles)
        return token_data

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# User database operations
async def get_user(db: AsyncSession, username: str) -> Optional[UserInDB]:
    """Get a user from the database by username"""
    # This is a placeholder - in production, query from the users table
    # For now, return a mock admin user for testing
    if username == "admin":
        return UserInDB(
            id=1,
            username="admin",
            email="admin@finance.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),  # Change in production!
            is_active=True,
            is_superuser=True,
            roles=[Role.ADMIN, Role.TRADER, Role.ANALYST]
        )
    elif username == "trader":
        return UserInDB(
            id=2,
            username="trader",
            email="trader@finance.com",
            full_name="Trader User",
            hashed_password=get_password_hash("trader123"),
            is_active=True,
            is_superuser=False,
            roles=[Role.TRADER]
        )
    elif username == "analyst":
        return UserInDB(
            id=3,
            username="analyst",
            email="analyst@finance.com",
            full_name="Analyst User",
            hashed_password=get_password_hash("analyst123"),
            is_active=True,
            is_superuser=False,
            roles=[Role.ANALYST]
        )

    return None


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user"""
    user = await get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# Dependency functions
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = decode_token(token)
        user = await get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# RBAC - Role-based access control
class RoleChecker:
    """Dependency to check if user has required role(s)"""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        """Check if user has one of the allowed roles"""
        if user.is_superuser:
            return user  # Superuser has all permissions

        user_roles = set(user.roles)
        allowed_roles = set(self.allowed_roles)

        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(self.allowed_roles)}"
            )

        return user


# Convenience functions for common role checks
require_admin = RoleChecker([Role.ADMIN])
require_trader = RoleChecker([Role.TRADER, Role.ADMIN])
require_analyst = RoleChecker([Role.ANALYST, Role.ADMIN])
require_any_authenticated = RoleChecker([Role.USER, Role.READONLY, Role.ANALYST, Role.TRADER, Role.ADMIN])


# Permission decorators
def require_permissions(*permissions: str):
    """Decorator to require specific permissions"""
    # This is a placeholder for a more sophisticated permission system
    # In production, you might have granular permissions like:
    # - "market_data:read"
    # - "trading:execute"
    # - "portfolio:manage"
    # - "admin:users"
    pass
