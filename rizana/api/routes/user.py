from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm

from rizana.api.controllers.user import UserController
from rizana.api.schemas.user import UserCreate, UserQuery
from rizana.dependencies import get_current_active_user, get_user_controller

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_user(
    query: Annotated[UserQuery, Query()],
    user_controller: UserController = Depends(get_user_controller),
):
    return await user_controller.get_user(query)


@router.get("/me")
async def get_current_user_info(
    current_user: UserController = Depends(get_current_active_user),
):
    return current_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_controller: UserController = Depends(get_user_controller),
):
    return await user_controller.login_user(form_data)


# @router.delete("/user/{user_id}", status_code=HTTP_204_NO_CONTENT)
# async def delete_user(user_id: UUID, user_controller: UserController = Depends(get_user_controller)):
#     await user_controller.delete_user(user_id)

# @router.put("/user/{user_id}", response_model=UserUpdate)
# async def update_user(user_id: UUID, user: UserUpdate, user_controller: UserController = Depends(get_user_controller)):
#     return await user_controller.update_user(user_id, user)


@router.post("/")
async def create_user(
    user: UserCreate, user_controller: UserController = Depends(get_user_controller)
):
    return await user_controller.create_user(user)
