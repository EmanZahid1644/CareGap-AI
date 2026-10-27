
import pytest

from backend.app.core.permissions import (
    Permission,
    has_permission,
)
from backend.app.models.identity import OrganizationRole


@pytest.mark.parametrize(
    "role, permission, expected",
    [
        (
            OrganizationRole.OWNER,
            Permission.STAFF_MANAGE,
            True,
        ),
        (
            OrganizationRole.OWNER,
            Permission.CLINICAL_WRITE,
            True,
        ),
        (
            OrganizationRole.ADMIN,
            Permission.STAFF_MANAGE,
            True,
        ),
        (
            OrganizationRole.ADMIN,
            Permission.CLINICAL_WRITE,
            False,
        ),
        (
            OrganizationRole.CLINICIAN,
            Permission.CLINICAL_WRITE,
            True,
        ),
        (
            OrganizationRole.CLINICIAN,
            Permission.STAFF_MANAGE,
            False,
        ),
        (
            OrganizationRole.REVIEWER,
            Permission.CLINICAL_READ,
            True,
        ),
        (
            OrganizationRole.REVIEWER,
            Permission.CLINICAL_WRITE,
            False,
        ),
        (
            OrganizationRole.VIEWER,
            Permission.CLINICAL_READ,
            True,
        ),
        (
            OrganizationRole.VIEWER,
            Permission.CLINICAL_WRITE,
            False,
        ),
    ],
)
def test_role_permissions(role, permission, expected):
    assert has_permission(role, permission) is expected
