from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from rizana.api.controllers.email import email_success
from rizana.api.controllers.user import UserController
from rizana.api.schemas.user import ActivateUser, UserCreate, UserQuery, UserView
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
) -> UserView:
    return await user_controller.get_user(query)


@router.get("/me")
async def get_current_user_info(
    current_user: UserController = Depends(get_current_active_user),
) -> UserView:
    return current_user


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_controller: UserController = Depends(get_user_controller),
):
    return await user_controller.login_user(form_data)


@router.post("/", response_model_exclude={"password"})
async def create_user(
    user: UserCreate, user_controller: UserController = Depends(get_user_controller)
) -> UserView:
    return await user_controller.create_user(user)


# @router.post("/logout")
# async def logout(
#     user_controller: UserController = Depends(get_user_controller),
#     current_user: UserController = Depends(get_current_active_user),
# ):
#     return await user_controller.logout_user(current_user)

# @router.post("/send-activation-email")
# async def send_activation_email(
#     user_query: UserQuery,
#     user_controller: UserController = Depends(get_user_controller),
# ):
#     return await user_controller.send_activation_email(user_query)


@router.get("/activate")
async def activate_user(
    activate_user_query: Annotated[ActivateUser, Query()],
    user_controller: UserController = Depends(get_user_controller),
):
    await user_controller.activate_user(
        activate_user_query.user_id, activate_user_query.activation_key
    )
    return HTMLResponse(content=email_success, status_code=200)
