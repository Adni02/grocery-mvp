"""
Seed script for service postcodes.
Covers Copenhagen and surrounding areas for Phase-1 MVP.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import async_session_maker
from app.models.address import ServicePostcode


# Copenhagen area postcodes with city names
POSTCODES = [
    # Copenhagen K (Center)
    {"postcode": "1000", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1050", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1100", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1150", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1200", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1250", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1300", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1350", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1400", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1450", "city": "København K", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1500", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1550", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1600", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1650", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1700", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1750", "city": "København V", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1800", "city": "Frederiksberg C", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1850", "city": "Frederiksberg C", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1900", "city": "Frederiksberg C", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "1950", "city": "Frederiksberg C", "delivery_fee": 0, "min_order_amount": 200},
    
    # Østerbro
    {"postcode": "2100", "city": "København Ø", "delivery_fee": 0, "min_order_amount": 200},
    
    # Nørrebro
    {"postcode": "2200", "city": "København N", "delivery_fee": 0, "min_order_amount": 200},
    
    # Nordvest
    {"postcode": "2400", "city": "København NV", "delivery_fee": 0, "min_order_amount": 200},
    
    # Valby
    {"postcode": "2500", "city": "Valby", "delivery_fee": 0, "min_order_amount": 200},
    
    # Vanløse
    {"postcode": "2720", "city": "Vanløse", "delivery_fee": 0, "min_order_amount": 200},
    
    # Brønshøj
    {"postcode": "2700", "city": "Brønshøj", "delivery_fee": 0, "min_order_amount": 200},
    
    # Amager
    {"postcode": "2300", "city": "København S", "delivery_fee": 0, "min_order_amount": 200},
    {"postcode": "2770", "city": "Kastrup", "delivery_fee": 29, "min_order_amount": 250},
    
    # Frederiksberg
    {"postcode": "2000", "city": "Frederiksberg", "delivery_fee": 0, "min_order_amount": 200},
    
    # Hellerup
    {"postcode": "2900", "city": "Hellerup", "delivery_fee": 29, "min_order_amount": 250},
    
    # Gentofte
    {"postcode": "2820", "city": "Gentofte", "delivery_fee": 29, "min_order_amount": 250},
    
    # Charlottenlund
    {"postcode": "2920", "city": "Charlottenlund", "delivery_fee": 29, "min_order_amount": 250},
]


async def seed_postcodes():
    """Insert or update service postcodes."""
    async with async_session_maker() as session:
        for pc_data in POSTCODES:
            # Check if postcode exists
            result = await session.execute(
                select(ServicePostcode).where(ServicePostcode.postcode == pc_data["postcode"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing
                existing.city = pc_data["city"]
                existing.delivery_fee = pc_data["delivery_fee"]
                existing.min_order_amount = pc_data["min_order_amount"]
                existing.is_active = True
                print(f"Updated: {pc_data['postcode']} - {pc_data['city']}")
            else:
                # Create new
                postcode = ServicePostcode(
                    postcode=pc_data["postcode"],
                    city=pc_data["city"],
                    delivery_fee=pc_data["delivery_fee"],
                    min_order_amount=pc_data["min_order_amount"],
                    is_active=True
                )
                session.add(postcode)
                print(f"Created: {pc_data['postcode']} - {pc_data['city']}")
        
        await session.commit()
        print(f"\n✓ Seeded {len(POSTCODES)} postcodes")


if __name__ == "__main__":
    asyncio.run(seed_postcodes())
