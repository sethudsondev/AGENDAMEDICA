import logging
import os
import secrets

logger = logging.getLogger(__name__)

_DEFAULT_SECRET_KEY = "dev-secret-key-change-me"


class Config:
    """Configurações da aplicação, lidas de variáveis de ambiente."""

    SECRET_KEY = os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY)
    if SECRET_KEY == _DEFAULT_SECRET_KEY:
        # Evita rodar em produção com a chave padrão (previsível) sem alertar.
        # Gera uma chave aleatória por processo em vez de usar a fixa,
        # e avisa no log para o operador corrigir a variável de ambiente.
        SECRET_KEY = secrets.token_hex(32)
        logger.warning(
            "SECRET_KEY não definida via variável de ambiente; usando uma chave "
            "aleatória gerada em tempo de execução (sessões não sobrevivem a "
            "reinícios do processo). Defina SECRET_KEY em produção."
        )

    # Banco de dados SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DB_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "agenda.db")
    )

    # API de agendamentos (pode ser um serviço separado ou endpoint mockado)
    #
    # AGENDAMENTOS_HOST tem prioridade: permite que plataformas como o Render
    # injetem apenas o hostname do serviço da API (via `fromService` em um
    # Blueprint) e a URL completa seja montada aqui, sem precisar copiar a
    # URL manualmente entre serviços.
    _agendamentos_host = os.environ.get("AGENDAMENTOS_HOST")
    if _agendamentos_host:
        AGENDAMENTOS_API_URL = f"https://{_agendamentos_host}/api/agendamentos"
    else:
        AGENDAMENTOS_API_URL = os.environ.get(
            "AGENDAMENTOS_API_URL", "http://localhost:5001/api/agendamentos"
        )
    API_TIMEOUT_SECONDS = float(os.environ.get("API_TIMEOUT_SECONDS", "5"))

    # Usuário de teste (usado apenas no script de seed)
    TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "teste@timesaver.com.br")
    TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "senha123")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Segurança de sessão/cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em produção atrás de HTTPS, defina SESSION_COOKIE_SECURE=1 via ambiente.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    # Evita que requisições muito grandes (ex.: formulários maliciosos) sejam
    # processadas sem limite.
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1 MB
