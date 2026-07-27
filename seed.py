"""Script de seed: cria as tabelas (se necessário) e o usuário de teste.

Uso:
    python seed.py
"""
import logging

from app.config import Config
from app.models.database import init_db
from app.models.usuario import criar_usuario

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    import os

    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    init_db(Config.DB_PATH)
    criar_usuario(Config.DB_PATH, Config.TEST_USER_EMAIL, Config.TEST_USER_PASSWORD, nome="Usuário de Teste")
    logger.info(
        "Usuário de teste pronto -> email: %s | senha: %s",
        Config.TEST_USER_EMAIL,
        Config.TEST_USER_PASSWORD,
    )


if __name__ == "__main__":
    main()
