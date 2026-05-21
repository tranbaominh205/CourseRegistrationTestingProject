import warnings
import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db

# Suppress ResourceWarnings from unclosed DB connections in tests
warnings.filterwarnings("ignore", category=ResourceWarning)


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        # Dispose of all connections after each test
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()