
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.session import engine
from backend.app.models.identity import (
    AccountType,
    Organization,
    OrganizationMembership,
    OrganizationRole,
    User,
)


@pytest.fixture
def db_session():
    """Provide a transaction that is rolled back after each test."""
    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


def test_database_connection():
    """Verify that PostgreSQL is reachable."""
    with engine.connect() as connection:
        result = connection.exec_driver_sql("SELECT 1")
        assert result.scalar_one() == 1


def test_create_and_read_user(db_session):
    """Create a user and read it back from the database."""
    unique_email = f"{uuid.uuid4().hex}@example.com"

    user = User(
        email=unique_email,
        full_name="Integration Test User",
        account_type=AccountType.PERSONAL,
        password_hash="test-only-hash",
    )

    db_session.add(user)
    db_session.flush()

    saved_user = db_session.scalar(
        select(User).where(User.email == unique_email)
    )

    assert saved_user is not None
    assert saved_user.id == user.id
    assert saved_user.email == unique_email
    assert saved_user.full_name == "Integration Test User"
    assert saved_user.account_type == AccountType.PERSONAL
    assert saved_user.password_hash == "test-only-hash"


def test_duplicate_email_is_rejected(db_session):
    """The database must reject duplicate user email addresses."""
    unique_email = f"{uuid.uuid4().hex}@example.com"

    first_user = User(
        email=unique_email,
        full_name="First Test User",
        account_type=AccountType.PERSONAL,
        password_hash="test-only-hash",
    )

    second_user = User(
        email=unique_email,
        full_name="Second Test User",
        account_type=AccountType.PERSONAL,
        password_hash="test-only-hash",
    )

    db_session.add(first_user)
    db_session.flush()

    db_session.add(second_user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_organization_membership(db_session):
    """Create a hospital user and link them to an organization."""
    user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        full_name="Hospital Staff Test",
        account_type=AccountType.HOSPITAL,
        password_hash="test-only-hash",
    )

    organization = Organization(
        name="Integration Test Hospital",
        slug=f"test-{uuid.uuid4().hex}",
    )

    db_session.add_all([user, organization])
    db_session.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=organization.id,
        role=OrganizationRole.CLINICIAN,
    )

    db_session.add(membership)
    db_session.flush()

    saved_membership = db_session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization.id,
        )
    )

    assert saved_membership is not None
    assert saved_membership.user_id == user.id
    assert saved_membership.organization_id == organization.id
    assert saved_membership.role == OrganizationRole.CLINICIAN


def test_duplicate_membership_is_rejected(db_session):
    """A user cannot have duplicate memberships in one organization."""
    user = User(
        email=f"{uuid.uuid4().hex}@example.com",
        full_name="Membership Test User",
        account_type=AccountType.HOSPITAL,
        password_hash="test-only-hash",
    )

    organization = Organization(
        name="Membership Test Hospital",
        slug=f"membership-{uuid.uuid4().hex}",
    )

    db_session.add_all([user, organization])
    db_session.flush()

    first_membership = OrganizationMembership(
        user_id=user.id,
        organization_id=organization.id,
        role=OrganizationRole.CLINICIAN,
    )

    second_membership = OrganizationMembership(
        user_id=user.id,
        organization_id=organization.id,
        role=OrganizationRole.VIEWER,
    )

    db_session.add(first_membership)
    db_session.flush()

    db_session.add(second_membership)

    with pytest.raises(IntegrityError):
        db_session.flush()
