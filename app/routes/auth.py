import logging
import time
from collections import defaultdict
from threading import Lock

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.database import DatabaseError
from app.models.usuario import validar_credenciais
from app.security import validar_csrf_token

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

# Proteção simples contra força bruta: limita tentativas de login por
# combinação de IP + e-mail em uma janela de tempo curta.
#
# Implementação em memória do processo -- adequada para uma única instância
# (como neste desafio). Em produção com múltiplas instâncias, isso
# precisaria ser compartilhado (ex.: Redis) para funcionar corretamente.
_JANELA_SEGUNDOS = 300
_MAX_TENTATIVAS = 5
_tentativas_login = defaultdict(list)
_lock_tentativas = Lock()


def _chave_tentativa(ip, email):
    return f"{ip}:{email.lower().strip()}"


def _bloqueado_por_tentativas(ip, email):
    chave = _chave_tentativa(ip, email)
    agora = time.time()
    with _lock_tentativas:
        tentativas = [t for t in _tentativas_login[chave] if agora - t < _JANELA_SEGUNDOS]
        _tentativas_login[chave] = tentativas
        return len(tentativas) >= _MAX_TENTATIVAS


def _registrar_tentativa_falha(ip, email):
    chave = _chave_tentativa(ip, email)
    with _lock_tentativas:
        _tentativas_login[chave].append(time.time())


def _limpar_tentativas(ip, email):
    chave = _chave_tentativa(ip, email)
    with _lock_tentativas:
        _tentativas_login.pop(chave, None)


@auth_bp.route("/", methods=["GET"])
def raiz():
    if session.get("usuario_id"):
        return redirect(url_for("agenda.principal"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    validar_csrf_token(request.form.get("csrf_token"))

    email = request.form.get("email", "")
    senha = request.form.get("senha", "")
    ip_cliente = request.remote_addr or "desconhecido"

    if not email.strip() or not senha:
        flash("Informe usuário/e-mail e senha.", "erro")
        return render_template("login.html"), 400

    if _bloqueado_por_tentativas(ip_cliente, email):
        logger.warning("Login bloqueado por excesso de tentativas: %s (%s)", email, ip_cliente)
        flash(
            "Muitas tentativas de login. Aguarde alguns minutos e tente novamente.",
            "erro",
        )
        return render_template("login.html"), 429

    try:
        usuario = validar_credenciais(current_app.config["DB_PATH"], email, senha)
    except DatabaseError:
        flash(
            "Não foi possível validar suas credenciais: erro de conexão com o banco de dados.",
            "erro",
        )
        return render_template("login.html"), 503

    if usuario is None:
        _registrar_tentativa_falha(ip_cliente, email)
        flash("Usuário ou senha inválidos.", "erro")
        return render_template("login.html"), 401

    _limpar_tentativas(ip_cliente, email)
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_email"] = usuario["email"]
    logger.info("Login bem-sucedido para %s", usuario["email"])
    return redirect(url_for("agenda.principal"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    validar_csrf_token(request.form.get("csrf_token"))
    session.clear()
    return redirect(url_for("auth.login"))
