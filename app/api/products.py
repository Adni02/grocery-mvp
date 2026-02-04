"""Product API routes."""

from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.dependencies import DbSession
from app.schemas.product import CategoryResponse, ProductListResponse, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: DbSession,
    page: int = 1,
    limit: int = 20,
    category: Optional[str] = None,
    q: Optional[str] = None,
    featured: Optional[bool] = None,
):
    """
    List products with optional filtering and pagination.

    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 20, max: 100)
    - **category**: Filter by category slug
    - **q**: Search query (searches name, description, SKU)
    - **featured**: Filter by featured status
    """
    # Validate pagination
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 20

    product_service = ProductService(db)

    products, total = await product_service.list_products(
        page=page,
        limit=limit,
        category_slug=category,
        search=q,
        is_featured=featured,
    )

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
        pages=product_service.calculate_pages(total, limit),
    )


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: DbSession):
    """
    List all active product categories.
    Returns a flat list of top-level categories with their children.
    """
    product_service = ProductService(db)
    categories = await product_service.list_categories()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.get("/{slug}", response_model=ProductResponse)
async def get_product(slug: str, db: DbSession):
    """
    Get a single product by its slug.
    """
    product_service = ProductService(db)
    product = await product_service.get_product_by_slug(slug)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse.model_validate(product)
