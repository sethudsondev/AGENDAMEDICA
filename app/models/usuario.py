import logging
from werkzeug.security import check_password_hash, generate_password_hash

from app.models.database import db_session, DatabaseError

logger = logging.getLogger(__name__)


def criar_usuario(db_path, email, senha, nome=None):
    senha_hash = generate_password_hash(senha)
    with db_session(db_path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO usuarios (email, senha_hash, nome) VALUES (?, ?, ?)",
            (email.lower().strip(), senha_hash, nome),
        )


def validar_credenciais(db_path, email, senha):
    """Retorna o dicionário do usuário se as credenciais forem válidas,
    ou None se forem inválidas. Propaga DatabaseError em caso de falha
    de conexão, para ser tratado na rota."""
    if not email or not senha:
        return None

    try:
        with db_session(db_path) as conn:
            row = conn.execute(
                "SELECT id, email, senha_hash, nome FROM usuarios WHERE email = ?",
                (email.lower().strip(),),
            ).fetchone()
    except DatabaseError:
        # Erro de conexão/consulta: repropaga para a rota decidir a mensagem
        raise

    if row is None:
        logger.info("Tentativa de login com e-mail não cadastrado: %s", email)
        return None

    if not check_password_hash(row["senha_hash"], senha):
        logger.info("Tentativa de login com senha incorreta para: %s", email)
        return None

    return {"id": row["id"], "email": row["email"], "nome": row["nome"]}
