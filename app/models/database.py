import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Erro genérico de acesso ao banco de dados, usado para tratamento
    controlado das falhas de conexão/consulta na camada de rotas."""


def get_connection(db_path):
    """Abre uma conexão SQLite. Lança DatabaseError em caso de falha,
    para que a camada de rotas trate isso de forma controlada."""
    try:
        conn = sqlite3.connect(db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as exc:
        logger.error("Falha ao conectar ao banco de dados (%s): %s", db_path, exc)
        raise DatabaseError("Não foi possível conectar ao banco de dados.") from exc


@contextmanager
def db_session(db_path):
    """Context manager que garante fechamento da conexão e traduz
    qualquer erro sqlite3 em DatabaseError."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback()
        logger.error("Erro durante operação no banco de dados: %s", exc)
        raise DatabaseError("Erro ao acessar o banco de dados.") from exc
    finally:
        conn.close()


def init_db(db_path):
    """Cria as tabelas necessárias caso não existam."""
    with db_session(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                nome TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Tabela local opcional de agendamentos, usada como cache/registro
        # do que foi recebido pela API na última sincronização.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agendamentos_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente TEXT NOT NULL,
                cpf TEXT NOT NULL,
                medico TEXT NOT NULL,
                especialidade TEXT,
                data TEXT,
                horario TEXT,
                convenio TEXT,
                status TEXT,
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    logger.info("Banco de dados inicializado em %s", db_path)
