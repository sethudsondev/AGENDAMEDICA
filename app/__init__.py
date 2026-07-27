import logging
import os

from flask import Flask

from app.config import Config
from app.models.database import init_db


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config_class)

    logging.basicConfig(
        level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    os.makedirs(os.path.dirname(app.config["DB_PATH"]), exist_ok=True)
    init_db(app.config["DB_PATH"])

    from app.routes.auth import auth_bp
    from app.routes.agenda import agenda_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(agenda_bp)

    @app.after_request
    def aplicar_cabecalhos_seguranca(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response

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
