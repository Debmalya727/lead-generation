from fastapi import APIRouter, Depends, status
from app.api.deps import get_auth_module
from app.modules.auth.auth_module import AuthModule
from app.schemas.auth import LoginRequest, RefreshRequest, TokenSchema
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
async def signup(
    signup_data: UserCreate,
    auth_module: AuthModule = Depends(get_auth_module)
):
    """Create a new user account in database after validating credentials."""
    return await auth_module.register_user(signup_data)


@router.post(
    "/login",
    response_model=TokenSchema,
    summary="User Login"
)
async def login(
    login_data: LoginRequest,
    auth_module: AuthModule = Depends(get_auth_module)
):
    """Authenticate credentials and return JWT Access + Refresh tokens."""
    return await auth_module.authenticate_user(login_data)


@router.post(
    "/refresh",
    response_model=TokenSchema,
    summary="Rotate Session Tokens"
)
async def refresh(
    refresh_data: RefreshRequest,
    auth_module: AuthModule = Depends(get_auth_module)
):
    """Receive a valid refresh token and output rotated session token credentials."""
    return await auth_module.refresh_user_tokens(refresh_data.refresh_token)


@router.post(
    "/logout",
    summary="Logout user session"
)
async def logout():
    """Invalidate local token credentials (client side clears memory)."""
    return {"status": "success", "message": "Successfully logged out user session."}
