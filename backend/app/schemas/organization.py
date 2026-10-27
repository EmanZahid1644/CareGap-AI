
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=200,
    )
    slug: str = Field(
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )
