"""Address schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PostcodeVerifyRequest(BaseModel):
    """Request to verify a postcode."""

    postcode: str = Field(..., min_length=4, max_length=10)


class PostcodeVerifyResponse(BaseModel):
    """Response for postcode verification."""

    valid: bool
    city_name: Optional[str] = None
    error: Optional[str] = None


class ServiceAddressResponse(BaseModel):
    """Known address within a service postcode."""

    id: int
    street_name: str
    building_numbers: Optional[str] = None

    model_config = {"from_attributes": True}


class AddressBase(BaseModel):
    """Base address schema."""

    postcode: str = Field(..., min_length=4, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)
    street: str = Field(..., min_length=1, max_length=255)
    building: Optional[str] = Field(None, max_length=50)
    floor: Optional[str] = Field(None, max_length=20)
    apartment: Optional[str] = Field(None, max_length=20)
    instructions: Optional[str] = None
    label: Optional[str] = Field(None, max_length=50)
    is_default: bool = False


class AddressCreate(AddressBase):
    """Create address schema."""

    pass


class AddressUpdate(BaseModel):
    """Update address schema."""

    street: Optional[str] = Field(None, min_length=1, max_length=255)
    building: Optional[str] = Field(None, max_length=50)
    floor: Optional[str] = Field(None, max_length=20)
    apartment: Optional[str] = Field(None, max_length=20)
    instructions: Optional[str] = None
    label: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = None


class AddressResponse(BaseModel):
    """Address response schema."""

    id: UUID
    label: Optional[str] = None
    postcode: str
    city: str
    street: str
    building: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    instructions: Optional[str] = None
    is_verified: bool
    is_default: bool
    full_address: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
