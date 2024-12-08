from uuid import UUID

from fastapi import APIRouter, Depends
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from rizana.api.controllers.chat import ChatController
from rizana.api.models.table import User
from rizana.api.schemas.chat import (ConversationResponse, MessageCreate,
                                     MessageResponse, ProposalCreate,
                                     ProposalResponse)
from rizana.dependencies import get_chat_controller, get_current_active_user

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.post("/message", status_code=HTTP_201_CREATED, response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    chat_controller: ChatController = Depends(get_chat_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await chat_controller.send_message(current_user.id, message)


@router.get("/history/{other_user_id}/{item_id}", response_model=ConversationResponse)
async def get_conversation(
    other_user_id: UUID,
    item_id: UUID,
    chat_controller: ChatController = Depends(get_chat_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await chat_controller.get_conversation(
        current_user.id, other_user_id, item_id
    )


@router.post("/proposal", status_code=HTTP_201_CREATED, response_model=ProposalResponse)
async def create_proposal(
    proposal: ProposalCreate,
    chat_controller: ChatController = Depends(get_chat_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await chat_controller.create_proposal(current_user.id, proposal)


@router.post("/proposal/{proposal_id}/accept", status_code=HTTP_200_OK)
async def accept_proposal(
    proposal_id: UUID,
    chat_controller: ChatController = Depends(get_chat_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await chat_controller.accept_proposal(proposal_id, current_user.id)


@router.post("/proposal/{proposal_id}/refuse", status_code=HTTP_200_OK)
async def refuse_proposal(
    proposal_id: UUID,
    chat_controller: ChatController = Depends(get_chat_controller),
    current_user: User = Depends(get_current_active_user),
):
    return await chat_controller.refuse_proposal(proposal_id, current_user.id)
