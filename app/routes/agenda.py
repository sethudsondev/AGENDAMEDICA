import logging
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.services.agendamentos_client import AgendamentosAPIError, buscar_agendamentos

logger = logging.getLogger(__name__)
agenda_bp = Blueprint("agenda", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@agenda_bp.route("/agenda", methods=["GET"])
@login_required
def principal():
    return render_template("agenda.html", usuario_email=session.get("usuario_email"))


@agenda_bp.route("/api/agendamentos", methods=["GET"])
@login_required
def listar_agendamentos():
    """Endpoint consumido pelo Tabulator no front-end. Busca os dados na
    API de agendamentos e aplica busca opcional por paciente, CPF ou médico."""
    termo = (request.args.get("busca") or "").strip().lower()

    try:
        agendamentos = buscar_agendamentos(
            current_app.config["AGENDAMENTOS_API_URL"],
            current_app.config["API_TIMEOUT_SECONDS"],
        )
    except AgendamentosAPIError as exc:
        logger.error("Falha ao buscar agendamentos: %s", exc)
        return jsonify({"erro": str(exc)}), 502

    if termo:
        # entradas vazias/inválidas simplesmente não filtram nada -- não
        # provocam erro interno
        agendamentos = [
            a
            for a in agendamentos
            if termo in str(a.get("paciente", "")).lower()
            or termo in str(a.get("cpf", "")).lower()
            or termo in str(a.get("medico", "")).lower()
        ]

    return jsonify({"agendamentos": agendamentos, "total": len(agendamentos)})
