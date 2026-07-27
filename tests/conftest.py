import os
import tempfile

import pytest

from app import create_app
from app.config import Config
from app.models.usuario import criar_usuario


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    class _Config(TestConfig):
        DB_PATH = db_path

    flask_app = create_app(_Config)
    criar_usuario(db_path, "teste@timesaver.com.br", "senha123", nome="Usuário Teste")

    yield flask_app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def cliente_logado(client):
    client.post(
        "/login",
        data={"email": "teste@timesaver.com.br", "senha": "senha123"},
        follow_redirects=True,
    )
    return client
