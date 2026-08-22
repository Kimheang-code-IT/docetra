import pytest

from app.main import create_app


@pytest.fixture(scope="session")
def app():
    return create_app()
