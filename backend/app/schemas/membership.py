
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.models.identity import OrganizationRole


class MembershipCreateRequest(BaseModel):
    user_id: UUID
    role: OrganizationRole


class MembershipRoleUpdateRequest(BaseModel):
    role: OrganizationRole


class MembershipResponse(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
