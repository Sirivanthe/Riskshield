# Authentication service
import os
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import db
from models import User, UserRole

JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user: User) -> str:
    """Create a JWT token for a user"""
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get the current authenticated user from JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Handle datetime serialization
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def init_demo_users():
    """Initialize demo users for testing"""
    demo_users = [
        {
            "email": "lod1@bank.com",
            "full_name": "John Smith",
            "role": UserRole.LOD1_USER,
            "business_unit": "Technology Risk",
            "password": "password123"
        },
        {
            "email": "lod2@bank.com",
            "full_name": "Sarah Johnson",
            "role": UserRole.LOD2_USER,
            "business_unit": "Compliance",
            "password": "password123"
        },
        {
            "email": "admin@bank.com",
            "full_name": "Admin User",
            "role": UserRole.ADMIN,
            "business_unit": "IT Security",
            "password": "admin123"
        }
    ]
    
    for demo_user in demo_users:
        existing = await db.users.find_one({"email": demo_user["email"]})
        if not existing:
            user = User(
                email=demo_user["email"],
                full_name=demo_user["full_name"],
                role=demo_user["role"],
                business_unit=demo_user["business_unit"]
            )
            user_doc = {
                **user.model_dump(),
                "password": hash_password(demo_user["password"])
            }
            user_doc['created_at'] = user_doc['created_at'].isoformat()
            await db.users.insert_one(user_doc)
