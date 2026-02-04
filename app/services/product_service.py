"""Product service for catalog operations."""

import math
from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Service for product and category operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(
        self,
        page: int = 1,
        limit: int = 20,
        category_slug: Optional[str] = None,
        search: Optional[str] = None,
        is_active: bool = True,
        is_featured: Optional[bool] = None,
    ) -> tuple[list[Product], int]:
        """List products with pagination and filters."""
        # Base query
        stmt = select(Product).options(selectinload(Product.category))

        # Apply filters
        if is_active:
            stmt = stmt.where(Product.is_active == True)  # noqa: E712

        if is_featured is not None:
            stmt = stmt.where(Product.is_featured == is_featured)

        if category_slug:
            stmt = stmt.join(Category).where(Category.slug == category_slug)

        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.description).like(search_term),
                    func.lower(Product.sku).like(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit).order_by(Product.name)

        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total

    async def get_product_by_slug(self, slug: str) -> Optional[Product]:
        """Get a single product by slug."""
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.slug == slug, Product.is_active == True)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get a single product by ID."""
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_products_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        """Get multiple products by IDs."""
        if not product_ids:
            return []

        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id.in_(product_ids))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_product(self, data: ProductCreate) -> Product:
        """Create a new product."""
        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def update_product(self, product_id: UUID, data: ProductUpdate) -> Optional[Product]:
        """Update a product."""
        product = await self.get_product_by_id(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: UUID) -> bool:
        """Soft-delete a product by setting is_active=False."""
        product = await self.get_product_by_id(product_id)
        if not product:
            return False

        product.is_active = False
        await self.db.flush()
        return True

    async def list_categories(self, include_inactive: bool = False) -> list[Category]:
        """List all categories."""
        stmt = select(Category).options(selectinload(Category.children))

        if not include_inactive:
            stmt = stmt.where(Category.is_active == True)  # noqa: E712

        # Only get top-level categories (parent_id is NULL)
        stmt = stmt.where(Category.parent_id.is_(None)).order_by(Category.sort_order)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get a category by slug."""
        stmt = (
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.slug == slug, Category.is_active == True)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def calculate_pages(total: int, limit: int) -> int:
        """Calculate total number of pages."""
        return math.ceil(total / limit) if limit > 0 else 0
