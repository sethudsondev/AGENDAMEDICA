import logging
import secrets

from flask import abort, current_app, session

logger = logging.getLogger(__name__)


def gerar_csrf_token():
    """Garante que exista um token CSRF na sessão atual e o retorna,
    para ser embutido nos formulários como campo oculto."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validar_csrf_token(token_recebido):
    """Valida o token CSRF enviado no formulário contra o da sessão,
    usando comparação em tempo constante. Aborta com 400 se inválido.

    Em modo de teste (app.testing / TESTING=True), a validação é
    ignorada -- mesmo padrão adotado pelo Flask-WTF, para não obrigar
    cada teste a simular o fluxo completo de obtenção do token."""
    if current_app.testing:
        return

    token_sessao = session.get("_csrf_token")
    if not token_sessao or not token_recebido or not secrets.compare_digest(
        token_sessao, token_recebido
    ):
        logger.warning("Token CSRF ausente ou inválido em requisição POST.")
        abort(400, description="Token de segurança inválido ou expirado. Recarregue a página e tente novamente.")
