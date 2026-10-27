
import os

# Set the test database before importing the application.
TEST_DATABASE_URL = (
    "postgresql+psycopg://postgres@localhost:5432/caregap_ai_test"
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.app.db.session import engine, get_db  # noqa: E402
from backend.app.main import app  # noqa: E402


def pytest_sessionstart(session):
    expected_database = "caregap_ai_test"

    if engine.url.database != expected_database:
        raise RuntimeError(
            "Unsafe database URL. Expected caregap_ai_test."
        )

    with engine.connect() as connection:
        actual_database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    if actual_database != expected_database:
        raise RuntimeError(
            f"Unsafe database connection: {actual_database}"
        )

    print(f"\nVerified test database: {actual_database}")


@pytest.fixture
def isolated_db():
    connection = engine.connect()
    transaction = connection.begin()

    db = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
    )

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        app.dependency_overrides.pop(get_db, None)
        db.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()
