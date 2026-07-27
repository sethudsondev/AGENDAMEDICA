import logging
import re
import time

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

# Retry com backoff exponencial para falhas transitórias (timeout, conexão
# recusada, erro 5xx). Erros 4xx e respostas malformadas NÃO são
# reprocessados, pois repetir não mudaria o resultado.
MAX_TENTATIVAS = 3
BACKOFF_BASE_SEGUNDOS = 0.5


class AgendamentosAPIError(Exception):
    """Erro controlado ao buscar agendamentos na API externa.
    A mensagem já é adequada para exibição ao usuário final."""


def _registro_valido(registro):
    """Verifica se um registro individual tem todos os campos obrigatórios
    não vazios e um CPF com formato minimamente plausível (11 dígitos).
    Usado para filtrar dados incompletos/corrompidos sem quebrar a app."""
    if not isinstance(registro, dict):
        return False
    for campo in CAMPOS_OBRIGATORIOS:
        if not str(registro.get(campo, "")).strip():
            return False

    cpf_digitos = re.sub(r"\D", "", str(registro.get("cpf", "")))
    if len(cpf_digitos) != 11:
        return False

    return True


def _requisitar_com_retry(api_url, timeout_seconds):
    """Executa a chamada HTTP com retry e backoff exponencial para falhas
    transitórias. Levanta AgendamentosAPIError após esgotar as tentativas."""
    ultimo_erro = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(api_url, timeout=timeout_seconds)
        except requests.exceptions.Timeout as exc:
            ultimo_erro = AgendamentosAPIError(
                "O serviço de agendamentos está demorando para responder. Tente novamente em instantes."
            )
            logger.warning(
                "Timeout ao chamar API de agendamentos (tentativa %d/%d): %s",
                tentativa, MAX_TENTATIVAS, exc,
            )
        except requests.exceptions.ConnectionError as exc:
            ultimo_erro = AgendamentosAPIError(
                "O serviço de agendamentos está indisponível no momento."
            )
            logger.warning(
                "Falha de conexão com API de agendamentos (tentativa %d/%d): %s",
                tentativa, MAX_TENTATIVAS, exc,
            )
        except requests.exceptions.RequestException as exc:
            # Erro inesperado (não é timeout nem conexão) -- não vale a pena
            # tentar de novo, provavelmente é um problema estrutural.
            logger.error("Erro inesperado ao chamar API de agendamentos: %s", exc)
            raise AgendamentosAPIError(
                "Não foi possível obter os agendamentos no momento."
            ) from exc
        else:
            if resposta.status_code >= 500:
                ultimo_erro = AgendamentosAPIError(
                    "O serviço de agendamentos está indisponível no momento."
                )
                logger.warning(
                    "API de agendamentos retornou erro %s (tentativa %d/%d)",
                    resposta.status_code, tentativa, MAX_TENTATIVAS,
                )
            elif resposta.status_code >= 400:
                # Erro do cliente (4xx): repetir não vai resolver.
                logger.error(
                    "API de agendamentos retornou erro do cliente %s", resposta.status_code
                )
                raise AgendamentosAPIError(
                    "Não foi possível obter os agendamentos (requisição inválida)."
                )
            else:
                return resposta

        if tentativa < MAX_TENTATIVAS:
            espera = BACKOFF_BASE_SEGUNDOS * (2 ** (tentativa - 1))
            time.sleep(espera)

    logger.error(
        "API de agendamentos indisponível após %d tentativas.", MAX_TENTATIVAS
    )
    raise ultimo_erro


def buscar_agendamentos(api_url, timeout_seconds):
    """Busca os agendamentos na API configurada.

    Trata explicitamente:
    - indisponibilidade temporária da API (timeout / connection error /
      erro 5xx), com retry automático e backoff exponencial
    - resposta HTTP de erro do cliente (4xx), sem retry
    - resposta vazia ou em formato inválido (não é JSON / não é lista)
    - campos obrigatórios ausentes em registros individuais (descarta o
      registro e loga um aviso, em vez de quebrar a aplicação inteira)
    """
    resposta = _requisitar_com_retry(api_url, timeout_seconds)

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
