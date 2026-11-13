"""Pytest fixtures: a fresh database schema and a test client for every test."""
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.db.models import Base
from app.main import app
from tests.helpers import TEST_ENGINE, override_get_db


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=TEST_ENGINE)
    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager, so the lifespan (PostgreSQL init) does not run.
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TEST_ENGINE)
