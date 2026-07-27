"""Ponto de entrada da Agenda Médica.

Uso:
    python run.py
"""
import logging
import os

from app import create_app
from app.services.agendamentos_client import AgendamentosAPIError, buscar_agendamentos

app = create_app()
logger = logging.getLogger(__name__)


def _checar_api_ao_iniciar():
    """Ao iniciar a aplicação pelo terminal, tenta buscar os dados da API
    de agendamentos e reporta o resultado no log -- confirmando que a
    aplicação entrega os dados assim que é iniciada."""
    try:
        agendamentos = buscar_agendamentos(
            app.config["AGENDAMENTOS_API_URL"], app.config["API_TIMEOUT_SECONDS"]
        )
        logger.info(
            "Verificação inicial da API de agendamentos: %d registro(s) disponível(is).",
            len(agendamentos),
        )
    except AgendamentosAPIError as exc:
        logger.warning(
            "Verificação inicial da API de agendamentos falhou (a aplicação seguirá "
            "disponível e tentará novamente a cada consulta): %s",
            exc,
        )


if __name__ == "__main__":
    _checar_api_ao_iniciar()
    porta = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=porta, debug=debug)
