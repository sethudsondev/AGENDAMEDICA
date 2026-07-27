import logging
import os

from flask import Flask, jsonify

from app.config import Config
from app.logging_utils import JsonFormatter
from app.models.database import DatabaseError, db_session, init_db
from app.security import gerar_csrf_token


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    _configurar_logging(app)

    os.makedirs(os.path.dirname(app.config["DB_PATH"]), exist_ok=True)
    init_db(app.config["DB_PATH"])

    from app.routes.auth import auth_bp
    from app.routes.agenda import agenda_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)

    @app.context_processor
    def injetar_csrf_token():
        return {"csrf_token": gerar_csrf_token}

    @app.after_request
    def aplicar_cabecalhos_seguranca(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

    @app.route("/health", methods=["GET"])
    def health():
        """Healthcheck para monitoramento externo (ex.: Render, load balancer).

        Verifica também a conectividade com o banco de dados -- um health
        endpoint que só confirma que o processo está de pé não é muito
        útil se o banco estiver inacessível."""
        try:
            with db_session(app.config["DB_PATH"]) as conn:
                conn.execute("SELECT 1")
        except DatabaseError:
            return jsonify({"status": "erro", "banco_de_dados": "indisponível"}), 503
        return jsonify({"status": "ok", "banco_de_dados": "ok"})

    @app.errorhandler(404)
    def not_found(_e):
        from flask import render_template

        return render_template("erro.html", mensagem="Página não encontrada."), 404

    @app.errorhandler(500)
    def erro_interno(e):
        from flask import render_template

        app.logger.error("Erro interno não tratado: %s", e)
        return (
            render_template(
                "erro.html",
                mensagem="Ocorreu um erro inesperado. Nossa equipe já foi notificada.",
            ),
            500,
        )

    return app


def _configurar_logging(app):
    handler = logging.StreamHandler()
    if os.environ.get("LOG_FORMAT", "text").lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, app.config["LOG_LEVEL"], logging.INFO))
