from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.database.mongodb.collections.user import User
from app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user details"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Retrieve logged-in user profile details mapped from active token subject."""
    return UserResponse.from_orm(current_user)
