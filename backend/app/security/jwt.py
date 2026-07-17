import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from app.config.settings import settings

logger = logging.getLogger("backend.security")

# Set standard expiration for refresh tokens (e.g. 7 days)
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT Access Token for the authenticated user ID."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Generate a signed JWT Refresh Token for the authenticated user ID."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Parse and validate a signed JWT token, returning its payload if valid."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: Signature has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token verification failed: Invalid token format: {str(e)}")
        return None
