"""Address API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.address import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
    PostcodeVerifyRequest,
    PostcodeVerifyResponse,
    ServiceAddressResponse,
)
from app.services.address_service import AddressService

router = APIRouter()


@router.post("/verify-postcode", response_model=PostcodeVerifyResponse)
async def verify_postcode(
    request: PostcodeVerifyRequest,
    db: DbSession,
    user: CurrentUser,
):
    """
    Verify if a postcode is within our delivery service area.

    Returns the city name if valid, or an error message if not serviceable.
    """
    address_service = AddressService(db)
    is_valid, city_name = await address_service.verify_postcode(request.postcode)

    if is_valid:
        return PostcodeVerifyResponse(valid=True, city_name=city_name)

    return PostcodeVerifyResponse(
        valid=False,
        error="We don't deliver to this area yet. Please check back later.",
    )


@router.get("/service-addresses", response_model=list[ServiceAddressResponse])
async def get_service_addresses(
    postcode: str,
    db: DbSession,
    user: CurrentUser,
):
    """
    Get known street addresses for a service postcode.

    This helps users select from verified addresses in our system.
    """
    address_service = AddressService(db)
    addresses = await address_service.get_service_addresses(postcode)
    return [ServiceAddressResponse.model_validate(a) for a in addresses]


@router.get("", response_model=list[AddressResponse])
async def list_addresses(
    db: DbSession,
    user: CurrentUser,
):
    """
    List all addresses for the current user.
    """
    address_service = AddressService(db)
    addresses = await address_service.get_user_addresses(user.id)
    return [AddressResponse.model_validate(a) for a in addresses]


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    data: AddressCreate,
    db: DbSession,
    user: CurrentUser,
):
    """
    Create a new address for the current user.

    The postcode will be verified against our service area.
    If valid, the address is marked as verified.
    """
    address_service = AddressService(db)

    try:
        address = await address_service.create_address(user.id, data)
        return AddressResponse.model_validate(address)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """
    Get a specific address by ID.
    """
    address_service = AddressService(db)
    address = await address_service.get_address_by_id(address_id, user.id)

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return AddressResponse.model_validate(address)


@router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    data: AddressUpdate,
    db: DbSession,
    user: CurrentUser,
):
    """
    Update an existing address.

    Note: Postcode and city cannot be changed. Create a new address for a different location.
    """
    address_service = AddressService(db)
    address = await address_service.update_address(address_id, user.id, data)

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return AddressResponse.model_validate(address)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    db: DbSession,
    user: CurrentUser,
):
    """
    Delete an address.

    Note: Addresses referenced by existing orders cannot be deleted.
    """
    address_service = AddressService(db)
    deleted = await address_service.delete_address(address_id, user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )
