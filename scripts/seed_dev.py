"""Quick seed script for development."""

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select


async def seed_all():
    """Seed postcodes and products."""
    # Import inside function to avoid circular imports
    from app.database import async_session_maker, init_db
    
    # Import ALL models to ensure relationships are registered
    from app.models.user import User
    from app.models.address import ServicePostcode, Address
    from app.models.product import Category, Product
    from app.models.cart import Cart, CartItem
    from app.models.order import Order, OrderItem
    
    print("Initializing database...")
    await init_db()
    
    async with async_session_maker() as session:
        # Seed postcodes
        postcodes = [
            {"postcode": "2100", "city": "København Ø"},
            {"postcode": "2200", "city": "København N"},
            {"postcode": "2000", "city": "Frederiksberg"},
            {"postcode": "1000", "city": "København K"},
            {"postcode": "2300", "city": "København S"},
        ]
        
        for pc in postcodes:
            result = await session.execute(
                select(ServicePostcode).where(ServicePostcode.postcode == pc["postcode"])
            )
            if not result.scalar_one_or_none():
                session.add(ServicePostcode(
                    postcode=pc["postcode"],
                    city=pc["city"],
                    delivery_fee=Decimal("0"),
                    min_order_amount=Decimal("200"),
                    is_active=True
                ))
                print(f"  + Postcode: {pc['postcode']} - {pc['city']}")
        
        # Seed categories
        categories_data = [
            {"name": "Frugt & Grønt", "slug": "frugt-gront", "sort_order": 1},
            {"name": "Mejeriprodukter", "slug": "mejeri", "sort_order": 2},
            {"name": "Brød & Bagværk", "slug": "brod", "sort_order": 3},
            {"name": "Kød & Fjerkræ", "slug": "kod", "sort_order": 4},
            {"name": "Drikkevarer", "slug": "drikkevarer", "sort_order": 5},
        ]
        
        categories = {}
        for cat in categories_data:
            result = await session.execute(
                select(Category).where(Category.slug == cat["slug"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                categories[cat["slug"]] = existing
            else:
                new_cat = Category(
                    name=cat["name"],
                    slug=cat["slug"],
                    sort_order=cat["sort_order"],
                    is_active=True
                )
                session.add(new_cat)
                await session.flush()
                categories[cat["slug"]] = new_cat
                print(f"  + Category: {cat['name']}")
        
        # Seed products
        products_data = [
            {"name": "Økologiske Bananer", "slug": "bananer", "price": "24.95", "category": "frugt-gront", "featured": True},
            {"name": "Danske Æbler", "slug": "aebler", "price": "19.95", "category": "frugt-gront", "featured": False},
            {"name": "Avocado", "slug": "avocado", "price": "12.95", "category": "frugt-gront", "featured": True},
            {"name": "Letmælk 1.5%", "slug": "letmaelk", "price": "12.50", "category": "mejeri", "featured": True},
            {"name": "Smør Lurpak", "slug": "smor", "price": "32.00", "category": "mejeri", "featured": True},
            {"name": "Skyr Naturel", "slug": "skyr", "price": "18.00", "category": "mejeri", "featured": False},
            {"name": "Rugbrød", "slug": "rugbrod", "price": "28.00", "category": "brod", "featured": True},
            {"name": "Franskbrød", "slug": "franskbrod", "price": "22.00", "category": "brod", "featured": False},
            {"name": "Hakket Oksekød", "slug": "hakket-oksekod", "price": "55.00", "category": "kod", "featured": True},
            {"name": "Kyllingebryst", "slug": "kyllingebryst", "price": "75.00", "category": "kod", "featured": True},
            {"name": "Appelsinjuice", "slug": "appelsinjuice", "price": "28.00", "category": "drikkevarer", "featured": False},
            {"name": "Kaffe Merrild", "slug": "kaffe", "price": "45.00", "category": "drikkevarer", "featured": True},
        ]
        
        for prod in products_data:
            result = await session.execute(
                select(Product).where(Product.slug == prod["slug"])
            )
            if not result.scalar_one_or_none():
                category = categories.get(prod["category"])
                session.add(Product(
                    name=prod["name"],
                    slug=prod["slug"],
                    price=Decimal(prod["price"]),
                    unit="stk",
                    category_id=category.id if category else None,
                    stock_quantity=100,
                    is_active=True,
                    is_featured=prod["featured"]
                ))
                print(f"  + Product: {prod['name']}")
        
        await session.commit()
        print("\n✓ Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_all())
