import logging

import requests

logger = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS = [
    "paciente",
    "cpf",
    "medico",
    "especialidade",
    "data",
    "horario",
    "convenio",
    "status",
]


class AgendamentosAPIError(Exception):
    """Erro controlado ao buscar agendamentos na API externa.
    A mensagem já é adequada para exibição ao usuário final."""


def _registro_valido(registro):
    """Verifica se um registro individual tem todos os campos obrigatórios
    não vazios. Usado para filtrar dados incompletos sem quebrar a app."""
    if not isinstance(registro, dict):
        return False
    for campo in CAMPOS_OBRIGATORIOS:
        if not str(registro.get(campo, "")).strip():
            return False
    return True


def buscar_agendamentos(api_url, timeout_seconds):
    """Busca os agendamentos na API configurada.

    Trata explicitamente:
    - indisponibilidade temporária da API (timeout / connection error)
    - resposta HTTP de erro (4xx/5xx)
    - resposta vazia ou em formato inválido (não é JSON / não é lista)
    - campos obrigatórios ausentes em registros individuais (descarta o
      registro e loga um aviso, em vez de quebrar a aplicação inteira)
    """
    try:
        resposta = requests.get(api_url, timeout=timeout_seconds)
    except requests.exceptions.Timeout as exc:
        logger.error("Timeout ao chamar API de agendamentos (%s): %s", api_url, exc)
        raise AgendamentosAPIError(
            "O serviço de agendamentos está demorando para responder. Tente novamente em instantes."
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        logger.error("Falha de conexão com API de agendamentos (%s): %s", api_url, exc)
        raise AgendamentosAPIError(
            "O serviço de agendamentos está indisponível no momento."
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Erro inesperado ao chamar API de agendamentos: %s", exc)
        raise AgendamentosAPIError(
            "Não foi possível obter os agendamentos no momento."
        ) from exc

    if resposta.status_code >= 500:
        logger.error("API de agendamentos retornou erro %s", resposta.status_code)
        raise AgendamentosAPIError(
            "O serviço de agendamentos está indisponível no momento."
        )
    if resposta.status_code >= 400:
        logger.error("API de agendamentos retornou erro do cliente %s", resposta.status_code)
        raise AgendamentosAPIError(
            "Não foi possível obter os agendamentos (requisição inválida)."
        )

    try:
        dados = resposta.json()
    except ValueError as exc:
        logger.error("Resposta da API de agendamentos não é um JSON válido: %s", exc)
        raise AgendamentosAPIError(
            "A resposta do serviço de agendamentos veio em formato inesperado."
        ) from exc

    if dados is None or dados == [] or dados == {}:
        logger.info("API de agendamentos retornou resposta vazia.")
        return []

    if isinstance(dados, dict) and "agendamentos" in dados:
        dados = dados["agendamentos"]

    if not isinstance(dados, list):
        logger.error("Resposta da API de agendamentos não é uma lista: %r", type(dados))
        raise AgendamentosAPIError(
            "A resposta do serviço de agendamentos veio em formato inesperado."
        )

    validos = []
    descartados = 0
    for registro in dados:
        if _registro_valido(registro):
            validos.append(registro)
        else:
            descartados += 1

    if descartados:
        logger.warning(
            "%d registro(s) descartado(s) por campos obrigatórios ausentes.", descartados
        )

    return validos
