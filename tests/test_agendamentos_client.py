import requests
import pytest

import app.services.agendamentos_client as agendamentos_client
from app.services.agendamentos_client import AgendamentosAPIError, buscar_agendamentos


@pytest.fixture(autouse=True)
def sem_espera_real(monkeypatch):
    """Evita que os testes de retry fiquem lentos esperando o backoff real."""
    monkeypatch.setattr(agendamentos_client.time, "sleep", lambda segundos: None)


class _RespostaFake:
    def __init__(self, status_code=200, payload=None, json_valido=True):
        self.status_code = status_code
        self._payload = payload
        self._json_valido = json_valido

    def json(self):
        if not self._json_valido:
            raise ValueError("payload inválido")
        return self._payload


def test_timeout_da_api_gera_erro_amigavel_apos_esgotar_tentativas(monkeypatch):
    chamadas = {"total": 0}

    def _timeout(*args, **kwargs):
        chamadas["total"] += 1
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", _timeout)

    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError as exc:
        assert "demorando" in str(exc)

    assert chamadas["total"] == agendamentos_client.MAX_TENTATIVAS


def test_conexao_recusada_gera_erro_amigavel(monkeypatch):
    def _conn_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, "get", _conn_error)

    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError as exc:
        assert "indisponível" in str(exc)


def test_retry_recupera_apos_falha_transitoria(monkeypatch):
    """A primeira tentativa falha (erro 503), a segunda funciona -- o
    retry deve entregar os dados normalmente, sem propagar o erro."""
    chamadas = {"total": 0}

    def _get(*args, **kwargs):
        chamadas["total"] += 1
        if chamadas["total"] == 1:
            return _RespostaFake(status_code=503)
        return _RespostaFake(status_code=200, payload=[])

    monkeypatch.setattr(requests, "get", _get)

    resultado = buscar_agendamentos("http://fake/api", 1)

    assert resultado == []
    assert chamadas["total"] == 2


def test_erro_4xx_nao_faz_retry(monkeypatch):
    """Erros do cliente (4xx) não devem ser reprocessados -- repetir a
    mesma requisição não mudaria o resultado."""
    chamadas = {"total": 0}

    def _get(*args, **kwargs):
        chamadas["total"] += 1
        return _RespostaFake(status_code=400)

    monkeypatch.setattr(requests, "get", _get)

    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError:
        pass

    assert chamadas["total"] == 1


def test_resposta_vazia_retorna_lista_vazia(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _RespostaFake(200, []))
    assert buscar_agendamentos("http://fake/api", 1) == []


def test_json_invalido_gera_erro(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: _RespostaFake(200, None, json_valido=False))
    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError:
        pass


def test_descarta_registro_com_cpf_em_formato_invalido(monkeypatch):
    payload = [
        {
            "paciente": "Maria",
            "cpf": "111.111.111-11",
            "medico": "Dr. João",
            "especialidade": "Cardiologia",
            "data": "2026-08-01",
            "horario": "09:00",
            "convenio": "Unimed",
            "status": "Confirmado",
        },
        {
            "paciente": "CPF Malformado",
            "cpf": "123",  # menos de 11 dígitos
            "medico": "Dr. João",
            "especialidade": "Cardiologia",
            "data": "2026-08-01",
            "horario": "11:00",
            "convenio": "Unimed",
            "status": "Confirmado",
        },
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: _RespostaFake(200, payload))
    resultado = buscar_agendamentos("http://fake/api", 1)
    assert len(resultado) == 1
    assert resultado[0]["paciente"] == "Maria"


def test_descarta_registro_com_campo_obrigatorio_ausente(monkeypatch):
    payload = [
        {
            "paciente": "Maria",
            "cpf": "111.111.111-11",
            "medico": "Dr. João",
            "especialidade": "Cardiologia",
            "data": "2026-08-01",
            "horario": "09:00",
            "convenio": "Unimed",
            "status": "Confirmado",
        },
        {
            "paciente": "Registro Incompleto",
            "cpf": "222",
            # 'medico' ausente
            "especialidade": "Dermatologia",
            "data": "2026-08-01",
            "horario": "10:00",
            "convenio": "Amil",
            "status": "Confirmado",
        },
    ]
    monkeypatch.setattr(requests, "get", lambda *a, **k: _RespostaFake(200, payload))
    resultado = buscar_agendamentos("http://fake/api", 1)
    assert len(resultado) == 1
    assert resultado[0]["paciente"] == "Maria"
