
import uuid

from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)


def test_account_types_exist():
    assert AccountType.PERSONAL.value == "personal"
    assert AccountType.HOSPITAL.value == "hospital"


def test_organization_roles_exist():
    assert OrganizationRole.OWNER.value == "owner"
    assert OrganizationRole.ADMIN.value == "admin"
    assert OrganizationRole.CLINICIAN.value == "clinician"
    assert OrganizationRole.REVIEWER.value == "reviewer"
    assert OrganizationRole.VIEWER.value == "viewer"


def test_identity_models_have_expected_tables():
    assert User.__tablename__ == "users"
    assert Organization.__tablename__ == "organizations"
    assert OrganizationMembership.__tablename__ == "organization_memberships"


def test_primary_keys_use_uuid_defaults():
    user = User(
        email="test@example.com",
        full_name="Test User",
        account_type=AccountType.PERSONAL,
    )

    organization = Organization(
        name="Test Hospital",
        slug="test-hospital",
    )

    membership = OrganizationMembership(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        role=OrganizationRole.VIEWER,
    )

    assert callable(User.__table__.c.id.default.arg)
    assert callable(Organization.__table__.c.id.default.arg)
    assert callable(OrganizationMembership.__table__.c.id.default.arg)
