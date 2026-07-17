import logging
from fastapi import HTTPException, status
from app.database.mongodb.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenSchema
from app.schemas.user import UserCreate, UserResponse
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password, verify_password

logger = logging.getLogger("backend.modules.auth")


class AuthModule:
    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    async def register_user(self, signup_data: UserCreate) -> UserResponse:
        """Register a new user, validating email uniqueness and hashing the password."""
        existing_user = await self.user_repo.get_by_email(signup_data.email)
        if existing_user:
            logger.warning(f"Registration conflict: Email {signup_data.email} is already in use.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address is already registered."
            )
        
        # Prepare hashed user fields
        user_dict = {
            "email": signup_data.email,
            "full_name": signup_data.full_name,
            "password_hash": hash_password(signup_data.password)
        }
        
        user = await self.user_repo.create(user_dict)
        logger.info(f"Successfully registered new user ID: {user.id}")
        return UserResponse.from_orm(user)

    async def authenticate_user(self, login_data: LoginRequest) -> TokenSchema:
        """Authenticate user credentials and issue signed access & refresh JWT tokens."""
        user = await self.user_repo.get_by_email(login_data.email)
        if not user:
            logger.warning(f"Authentication failed: Email {login_data.email} not found.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email address or password."
            )
        
        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Authentication failed: Incorrect password for {login_data.email}.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email address or password."
            )
        
        if not user.is_active:
            logger.warning(f"Authentication failed: User account {user.id} is deactivated.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your user account is currently deactivated."
            )
        
        # Generate token credentials
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        logger.info(f"Successful login for user ID: {user.id}")
        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def refresh_user_tokens(self, refresh_token: str) -> TokenSchema:
        """Validate the refresh token, and generate rotated access & refresh tokens."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            logger.warning("Token rotation failed: Invalid or expired refresh token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session refresh token."
            )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token rotation failed: Missing user subject in payload.")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invalid session token payload."
            )
        
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            logger.warning(f"Token rotation failed: User {user_id} not found or inactive.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account associated with this session is inactive or deleted."
            )
        
        # Rotate token family credentials
        new_access = create_access_token(str(user.id))
        new_refresh = create_refresh_token(str(user.id))
        
        logger.info(f"Rotated tokens successfully for user ID: {user.id}")
        return TokenSchema(
            access_token=new_access,
            refresh_token=new_refresh
        )
