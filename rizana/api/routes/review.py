from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from rizana.api.controllers.review import ReviewController
from rizana.api.schemas.review import ReviewCreate, ReviewUpdate, ReviewView
from rizana.dependencies import get_review_controller

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{review_id}", response_model=ReviewView)
async def get_review(
    review_id: int,
    review_controller: ReviewController = Depends(get_review_controller),
) -> ReviewView:
    """Get a review by ID.

    Args:
        review_id: The review's ID.
        review_controller: The review controller.

    Returns:
        ReviewView: The review details.
    """
    return await review_controller.get_by_id(review_id)


@router.get("/user/{user_id}", response_model=List[ReviewView])
async def get_reviews_by_user(
    user_id: int,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    review_controller: ReviewController = Depends(get_review_controller),
) -> List[ReviewView]:
    """Get reviews by user ID.

    Args:
        user_id: The user's ID.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        review_controller: The review controller.

    Returns:
        List[ReviewView]: List of reviews.
    """
    return await review_controller.get_by_user(user_id, skip, limit)


@router.get("/store/{store_id}", response_model=List[ReviewView])
async def get_reviews_by_store(
    store_id: int,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    review_controller: ReviewController = Depends(get_review_controller),
) -> List[ReviewView]:
    """Get reviews by store ID.

    Args:
        store_id: The store's ID.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        review_controller: The review controller.

    Returns:
        List[ReviewView]: List of reviews.
    """
    return await review_controller.get_by_store(store_id, skip, limit)


@router.post("/", response_model=ReviewView)
async def create_review(
    review: ReviewCreate,
    review_controller: ReviewController = Depends(get_review_controller),
) -> ReviewView:
    """Create a new review.

    Args:
        review: The review creation data.
        review_controller: The review controller.

    Returns:
        ReviewView: The created review.
    """
    return await review_controller.create(review)


@router.put("/{review_id}", response_model=ReviewView)
async def update_review(
    review_id: int,
    review: ReviewUpdate,
    review_controller: ReviewController = Depends(get_review_controller),
) -> ReviewView:
    """Update a review.

    Args:
        review_id: The review's ID.
        review: The review update data.
        review_controller: The review controller.

    Returns:
        ReviewView: The updated review.
    """
    return await review_controller.update(review_id, review)


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    review_controller: ReviewController = Depends(get_review_controller),
) -> None:
    """Delete a review.

    Args:
        review_id: The review's ID.
        review_controller: The review controller.
    """
    await review_controller.delete(review_id) 