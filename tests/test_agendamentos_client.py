import requests

from app.services.agendamentos_client import AgendamentosAPIError, buscar_agendamentos


class _RespostaFake:
    def __init__(self, status_code=200, payload=None, json_valido=True):
        self.status_code = status_code
        self._payload = payload
        self._json_valido = json_valido

    def json(self):
        if not self._json_valido:
            raise ValueError("payload inválido")
        return self._payload


def test_timeout_da_api_gera_erro_amigavel(monkeypatch):
    def _timeout(*args, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", _timeout)

    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError as exc:
        assert "demorando" in str(exc)


def test_conexao_recusada_gera_erro_amigavel(monkeypatch):
    def _conn_error(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(requests, "get", _conn_error)

    try:
        buscar_agendamentos("http://fake/api", 1)
        assert False, "deveria ter levantado AgendamentosAPIError"
    except AgendamentosAPIError as exc:
        assert "indisponível" in str(exc)


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


def test_descarta_registro_com_campo_obrigatorio_ausente(monkeypatch):
    payload = [
        {
            "paciente": "Maria",
            "cpf": "111",
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
