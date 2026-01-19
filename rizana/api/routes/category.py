from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from rizana.api.controllers.category import CategoryController
from rizana.api.schemas.category import CategoryCreate, CategoryUpdate, CategoryView
from rizana.dependencies import get_category_controller

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[CategoryView])
async def get_categories(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    category_controller: CategoryController = Depends(get_category_controller),
) -> List[CategoryView]:
    """Get all categories.

    Args:
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        category_controller: The category controller.

    Returns:
        List[CategoryView]: List of categories.
    """
    return await category_controller.get_all(skip, limit)


@router.get("/{category_id}", response_model=CategoryView)
async def get_category(
    category_id: int,
    category_controller: CategoryController = Depends(get_category_controller),
) -> CategoryView:
    """Get a category by ID.

    Args:
        category_id: The category's ID.
        category_controller: The category controller.

    Returns:
        CategoryView: The category details.
    """
    return await category_controller.get_by_id(category_id)


@router.post("/", response_model=CategoryView)
async def create_category(
    category: CategoryCreate,
    category_controller: CategoryController = Depends(get_category_controller),
) -> CategoryView:
    """Create a new category.

    Args:
        category: The category creation data.
        category_controller: The category controller.

    Returns:
        CategoryView: The created category.
    """
    return await category_controller.create(category)


@router.put("/{category_id}", response_model=CategoryView)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    category_controller: CategoryController = Depends(get_category_controller),
) -> CategoryView:
    """Update a category.

    Args:
        category_id: The category's ID.
        category: The category update data.
        category_controller: The category controller.

    Returns:
        CategoryView: The updated category.
    """
    return await category_controller.update(category_id, category)


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    category_controller: CategoryController = Depends(get_category_controller),
) -> None:
    """Delete a category.

    Args:
        category_id: The category's ID.
        category_controller: The category controller.
    """
    await category_controller.delete(category_id)
