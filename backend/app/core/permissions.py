
from enum import Enum

from backend.app.models.identity import OrganizationRole


class Permission(str, Enum):
    ORGANIZATION_MANAGE = "organization:manage"
    STAFF_READ = "staff:read"
    STAFF_MANAGE = "staff:manage"
    CLINICAL_READ = "clinical:read"
    CLINICAL_WRITE = "clinical:write"


ROLE_PERMISSIONS: dict[
    OrganizationRole, frozenset[Permission]
] = {
    OrganizationRole.OWNER: frozenset({
        Permission.ORGANIZATION_MANAGE,
        Permission.STAFF_READ,
        Permission.STAFF_MANAGE,
        Permission.CLINICAL_READ,
        Permission.CLINICAL_WRITE,
    }),

    OrganizationRole.ADMIN: frozenset({
        Permission.ORGANIZATION_MANAGE,
        Permission.STAFF_READ,
        Permission.STAFF_MANAGE,
        Permission.CLINICAL_READ,
    }),

    OrganizationRole.CLINICIAN: frozenset({
        Permission.STAFF_READ,
        Permission.CLINICAL_READ,
        Permission.CLINICAL_WRITE,
    }),

    OrganizationRole.REVIEWER: frozenset({
        Permission.STAFF_READ,
        Permission.CLINICAL_READ,
    }),

    OrganizationRole.VIEWER: frozenset({
        Permission.STAFF_READ,
        Permission.CLINICAL_READ,
    }),
}


def has_permission(
    role: OrganizationRole,
    permission: Permission,
) -> bool:
    return permission in ROLE_PERMISSIONS.get(
        role,
        frozenset(),
    )
