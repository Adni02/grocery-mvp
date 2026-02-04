"""
Seed script for sample products and categories.
Creates realistic Danish grocery products for testing.
"""
import asyncio
import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_maker
from app.models.product import Category, Product


CATEGORIES = [
    {"name": "Frugt & Grønt", "slug": "frugt-gront", "sort_order": 1},
    {"name": "Mejeriprodukter", "slug": "mejeri", "sort_order": 2},
    {"name": "Brød & Bagværk", "slug": "brod-bagvaerk", "sort_order": 3},
    {"name": "Kød & Fjerkræ", "slug": "kod-fjerkrae", "sort_order": 4},
    {"name": "Fisk & Skaldyr", "slug": "fisk-skaldyr", "sort_order": 5},
    {"name": "Kolonial", "slug": "kolonial", "sort_order": 6},
    {"name": "Drikkevarer", "slug": "drikkevarer", "sort_order": 7},
    {"name": "Frost", "slug": "frost", "sort_order": 8},
    {"name": "Snacks & Slik", "slug": "snacks-slik", "sort_order": 9},
    {"name": "Husholdning", "slug": "husholdning", "sort_order": 10},
]


PRODUCTS = [
    # Frugt & Grønt
    {"name": "Økologiske Bananer", "slug": "oko-bananer", "category_slug": "frugt-gront", 
     "price": 24.95, "unit": "bundt", "stock": 100, "is_featured": True,
     "description": "Lækre økologiske bananer fra Ecuador. Perfekte til madpakken eller smoothien."},
    {"name": "Danske Æbler", "slug": "danske-aebler", "category_slug": "frugt-gront",
     "price": 19.95, "unit": "pose", "stock": 80, "is_featured": False,
     "description": "Sprøde danske æbler fra Fyn. Pose med ca. 6 stk."},
    {"name": "Avocado", "slug": "avocado", "category_slug": "frugt-gront",
     "price": 12.95, "unit": "stk", "stock": 60, "is_featured": True,
     "description": "Modne avocadoer klar til at spise."},
    {"name": "Cherry Tomater", "slug": "cherry-tomater", "category_slug": "frugt-gront",
     "price": 22.00, "unit": "bakke", "stock": 50, "is_featured": False,
     "description": "Søde cherrytomater fra Spanien. 250g bakke."},
    {"name": "Salathoved Iceberg", "slug": "salat-iceberg", "category_slug": "frugt-gront",
     "price": 15.00, "unit": "stk", "stock": 40, "is_featured": False,
     "description": "Frisk og sprød icebergsalat."},
    {"name": "Agurk", "slug": "agurk", "category_slug": "frugt-gront",
     "price": 10.00, "unit": "stk", "stock": 70, "is_featured": False,
     "description": "Dansk drivhusagurk."},
    {"name": "Kartofler", "slug": "kartofler", "category_slug": "frugt-gront",
     "price": 18.00, "unit": "kg", "stock": 100, "is_featured": False,
     "description": "Danske kartofler. Posen vejer ca. 2 kg."},
    {"name": "Løg Net", "slug": "log-net", "category_slug": "frugt-gront",
     "price": 12.00, "unit": "net", "stock": 60, "is_featured": False,
     "description": "Net med danske løg, ca. 1 kg."},
    
    # Mejeriprodukter
    {"name": "Letmælk 1.5%", "slug": "letmaelk", "category_slug": "mejeri",
     "price": 12.50, "unit": "liter", "stock": 100, "is_featured": True,
     "description": "Arla letmælk 1.5% fedt. 1 liter karton."},
    {"name": "Skyr Naturel", "slug": "skyr-naturel", "category_slug": "mejeri",
     "price": 18.00, "unit": "bøtte", "stock": 60, "is_featured": False,
     "description": "Dansk skyr uden tilsat sukker. 450g bøtte."},
    {"name": "Smør Lurpak", "slug": "smor-lurpak", "category_slug": "mejeri",
     "price": 32.00, "unit": "stk", "stock": 50, "is_featured": True,
     "description": "Klassisk dansk smør. 200g pakke."},
    {"name": "Ost Riberhus", "slug": "ost-riberhus", "category_slug": "mejeri",
     "price": 45.00, "unit": "stk", "stock": 40, "is_featured": False,
     "description": "Dansk mellemlagret ost. 450g pakke."},
    {"name": "Æg Økologiske", "slug": "aeg-oko", "category_slug": "mejeri",
     "price": 42.00, "unit": "bakke", "stock": 80, "is_featured": False,
     "description": "10 stk økologiske æg fra fritgående høns."},
    {"name": "Fløde 38%", "slug": "flode", "category_slug": "mejeri",
     "price": 16.00, "unit": "bøtte", "stock": 50, "is_featured": False,
     "description": "Piskeflødе 38% fedt. 500ml bøtte."},
    
    # Brød & Bagværk  
    {"name": "Rugbrød Skovmand", "slug": "rugbrod-skovmand", "category_slug": "brod-bagvaerk",
     "price": 28.00, "unit": "stk", "stock": 30, "is_featured": True,
     "description": "Klassisk dansk rugbrød med solsikkekerner."},
    {"name": "Franskbrød", "slug": "franskbrod", "category_slug": "brod-bagvaerk",
     "price": 22.00, "unit": "stk", "stock": 40, "is_featured": False,
     "description": "Friskbagt franskbrød med sprød skorpe."},
    {"name": "Boller", "slug": "boller", "category_slug": "brod-bagvaerk",
     "price": 25.00, "unit": "pose", "stock": 35, "is_featured": False,
     "description": "Pose med 6 friskbagte boller."},
    {"name": "Croissanter", "slug": "croissanter", "category_slug": "brod-bagvaerk",
     "price": 30.00, "unit": "pose", "stock": 25, "is_featured": False,
     "description": "4 stk smørbagte croissanter."},
    
    # Kød & Fjerkræ
    {"name": "Hakket Oksekød 8-12%", "slug": "hakket-oksekod", "category_slug": "kod-fjerkrae",
     "price": 55.00, "unit": "pakke", "stock": 40, "is_featured": True,
     "description": "Dansk hakket oksekød, 8-12% fedt. 500g pakke."},
    {"name": "Kyllingebryst", "slug": "kyllingebryst", "category_slug": "kod-fjerkrae",
     "price": 75.00, "unit": "pakke", "stock": 35, "is_featured": True,
     "description": "Dansk kyllingebryst uden skind. Ca. 500g."},
    {"name": "Bacon Skiveskåret", "slug": "bacon", "category_slug": "kod-fjerkrae",
     "price": 35.00, "unit": "pakke", "stock": 50, "is_featured": False,
     "description": "Dansk skiveskåret bacon. 200g pakke."},
    {"name": "Frikadellefars", "slug": "frikadellefars", "category_slug": "kod-fjerkrae",
     "price": 45.00, "unit": "pakke", "stock": 30, "is_featured": False,
     "description": "Klassisk dansk frikadellefars. 500g pakke."},
    
    # Kolonial
    {"name": "Pasta Spaghetti", "slug": "pasta-spaghetti", "category_slug": "kolonial",
     "price": 12.00, "unit": "pakke", "stock": 100, "is_featured": False,
     "description": "Italiensk spaghetti. 500g pakke."},
    {"name": "Ris Basmati", "slug": "ris-basmati", "category_slug": "kolonial",
     "price": 25.00, "unit": "pose", "stock": 80, "is_featured": False,
     "description": "Aromatisk basmatiris. 1 kg pose."},
    {"name": "Hakkede Tomater", "slug": "hakkede-tomater", "category_slug": "kolonial",
     "price": 10.00, "unit": "dåse", "stock": 120, "is_featured": False,
     "description": "Italienske hakkede tomater. 400g dåse."},
    {"name": "Olivenolie Extra Virgin", "slug": "olivenolie", "category_slug": "kolonial",
     "price": 65.00, "unit": "flaske", "stock": 40, "is_featured": True,
     "description": "Koldpresset olivenolie fra Italien. 500ml."},
    {"name": "Kokosmælk", "slug": "kokosmaelk", "category_slug": "kolonial",
     "price": 18.00, "unit": "dåse", "stock": 60, "is_featured": False,
     "description": "Cremet kokosmælk. 400ml dåse."},
    
    # Drikkevarer
    {"name": "Juice Appelsin", "slug": "juice-appelsin", "category_slug": "drikkevarer",
     "price": 28.00, "unit": "liter", "stock": 50, "is_featured": False,
     "description": "Friskpresset appelsinjuice. 1 liter karton."},
    {"name": "Kaffe Merrild", "slug": "kaffe-merrild", "category_slug": "drikkevarer",
     "price": 45.00, "unit": "pose", "stock": 40, "is_featured": True,
     "description": "Malet filterkaffe. 400g pose."},
    {"name": "Kildevand", "slug": "kildevand", "category_slug": "drikkevarer",
     "price": 8.00, "unit": "flaske", "stock": 100, "is_featured": False,
     "description": "Dansk kildevand. 1.5 liter flaske."},
    {"name": "Coca-Cola", "slug": "coca-cola", "category_slug": "drikkevarer",
     "price": 20.00, "unit": "flaske", "stock": 80, "is_featured": False,
     "description": "Klassisk cola. 1.5 liter flaske + pant."},
    
    # Frost
    {"name": "Frostvarer Ærter", "slug": "frost-aerter", "category_slug": "frost",
     "price": 18.00, "unit": "pose", "stock": 60, "is_featured": False,
     "description": "Frosne grønne ærter. 450g pose."},
    {"name": "Pommes Frites", "slug": "pommes-frites", "category_slug": "frost",
     "price": 22.00, "unit": "pose", "stock": 50, "is_featured": False,
     "description": "Klassiske pommes frites til ovn. 750g pose."},
    {"name": "Is Vanilje", "slug": "is-vanilje", "category_slug": "frost",
     "price": 35.00, "unit": "bøtte", "stock": 30, "is_featured": True,
     "description": "Cremе is med vaniljesmag. 500ml bøtte."},
    
    # Snacks & Slik
    {"name": "Chips Sour Cream", "slug": "chips-sour-cream", "category_slug": "snacks-slik",
     "price": 25.00, "unit": "pose", "stock": 60, "is_featured": False,
     "description": "Sprøde chips med sour cream smag. 175g."},
    {"name": "Chokolade Marabou", "slug": "chokolade-marabou", "category_slug": "snacks-slik",
     "price": 32.00, "unit": "plade", "stock": 50, "is_featured": True,
     "description": "Klassisk mælkechokolade. 200g plade."},
    {"name": "Nøddemix", "slug": "noddemix", "category_slug": "snacks-slik",
     "price": 40.00, "unit": "pose", "stock": 40, "is_featured": False,
     "description": "Blanding af ristede nødder. 200g pose."},
]


async def seed_products():
    """Insert categories and products."""
    async with async_session_maker() as session:
        # Create categories
        category_map = {}
        for cat_data in CATEGORIES:
            result = await session.execute(
                select(Category).where(Category.slug == cat_data["slug"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                category_map[cat_data["slug"]] = existing
                print(f"Category exists: {cat_data['name']}")
            else:
                category = Category(
                    name=cat_data["name"],
                    slug=cat_data["slug"],
                    sort_order=cat_data["sort_order"],
                    is_active=True
                )
                session.add(category)
                await session.flush()
                category_map[cat_data["slug"]] = category
                print(f"Created category: {cat_data['name']}")
        
        # Create products
        for prod_data in PRODUCTS:
            result = await session.execute(
                select(Product).where(Product.slug == prod_data["slug"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"Product exists: {prod_data['name']}")
                continue
            
            category = category_map.get(prod_data["category_slug"])
            
            product = Product(
                name=prod_data["name"],
                slug=prod_data["slug"],
                description=prod_data.get("description"),
                price=Decimal(str(prod_data["price"])),
                unit=prod_data.get("unit", "stk"),
                category_id=category.id if category else None,
                stock_quantity=prod_data.get("stock", 0),
                is_active=True,
                is_featured=prod_data.get("is_featured", False)
            )
            session.add(product)
            print(f"Created product: {prod_data['name']}")
        
        await session.commit()
        print(f"\n✓ Seeded {len(CATEGORIES)} categories and {len(PRODUCTS)} products")


if __name__ == "__main__":
    asyncio.run(seed_products())
