"""Address service for address management and verification."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address, ServiceAddress, ServicePostcode
from app.schemas.address import AddressCreate, AddressUpdate


class AddressService:
    """Service for address verification and management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_postcode(self, postcode: str) -> tuple[bool, Optional[str]]:
        """
        Verify if a postcode is in the service area.
        Returns (is_valid, city_name).
        """
        stmt = select(ServicePostcode).where(
            ServicePostcode.postcode == postcode,
            ServicePostcode.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        service_postcode = result.scalar_one_or_none()

        if service_postcode:
            return True, service_postcode.city_name
        return False, None

    async def get_service_addresses(self, postcode: str) -> list[ServiceAddress]:
        """Get known addresses for a service postcode."""
        stmt = (
            select(ServiceAddress)
            .join(ServicePostcode)
            .where(
                ServicePostcode.postcode == postcode,
                ServicePostcode.is_active == True,  # noqa: E712
            )
            .order_by(ServiceAddress.street_name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_addresses(self, user_id: UUID) -> list[Address]:
        """Get all addresses for a user."""
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_address_by_id(self, address_id: UUID, user_id: UUID) -> Optional[Address]:
        """Get a specific address by ID, ensuring it belongs to the user."""
        stmt = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_verified_address(self, address_id: UUID, user_id: UUID) -> Optional[Address]:
        """Get an address only if it exists, belongs to user, and is verified."""
        stmt = select(Address).where(
            Address.id == address_id,
            Address.user_id == user_id,
            Address.is_verified == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_verified_address(self, user_id: UUID) -> bool:
        """Check if user has at least one verified address."""
        stmt = select(Address.id).where(
            Address.user_id == user_id,
            Address.is_verified == True,  # noqa: E712
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_address(self, user_id: UUID, data: AddressCreate) -> Address:
        """Create a new address for a user."""
        # Verify postcode first
        is_valid, city_name = await self.verify_postcode(data.postcode)
        if not is_valid:
            raise ValueError(f"Postcode {data.postcode} is not in our service area")

        # If this is set as default, unset other defaults
        if data.is_default:
            await self._unset_default_addresses(user_id)

        address = Address(
            user_id=user_id,
            is_verified=True,  # Verified because postcode is in allowlist
            **data.model_dump(),
        )
        self.db.add(address)
        await self.db.flush()
        await self.db.refresh(address)
        return address

    async def update_address(
        self, address_id: UUID, user_id: UUID, data: AddressUpdate
    ) -> Optional[Address]:
        """Update an existing address."""
        address = await self.get_address_by_id(address_id, user_id)
        if not address:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle default flag
        if update_data.get("is_default") is True:
            await self._unset_default_addresses(user_id)

        for field, value in update_data.items():
            setattr(address, field, value)

        await self.db.flush()
        await self.db.refresh(address)
        return address

    async def delete_address(self, address_id: UUID, user_id: UUID) -> bool:
        """Delete an address."""
        address = await self.get_address_by_id(address_id, user_id)
        if not address:
            return False

        await self.db.delete(address)
        await self.db.flush()
        return True

    async def _unset_default_addresses(self, user_id: UUID) -> None:
        """Unset the default flag on all user's addresses."""
        stmt = (
            update(Address)
            .where(Address.user_id == user_id, Address.is_default == True)  # noqa: E712
            .values(is_default=False)
        )
        await self.db.execute(stmt)

    # Admin methods for managing service postcodes

    async def list_service_postcodes(self) -> list[ServicePostcode]:
        """List all service postcodes."""
        stmt = select(ServicePostcode).order_by(ServicePostcode.postcode)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_service_postcode(self, postcode: str, city_name: str) -> ServicePostcode:
        """Add a new service postcode."""
        service_postcode = ServicePostcode(postcode=postcode, city_name=city_name)
        self.db.add(service_postcode)
        await self.db.flush()
        await self.db.refresh(service_postcode)
        return service_postcode

    async def remove_service_postcode(self, postcode_id: int) -> bool:
        """Remove a service postcode."""
        stmt = select(ServicePostcode).where(ServicePostcode.id == postcode_id)
        result = await self.db.execute(stmt)
        service_postcode = result.scalar_one_or_none()

        if not service_postcode:
            return False

        await self.db.delete(service_postcode)
        await self.db.flush()
        return True
