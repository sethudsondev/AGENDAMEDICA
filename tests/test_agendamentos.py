from app.services.agendamentos_client import AgendamentosAPIError


def test_listar_agendamentos_sem_resultados(cliente_logado, monkeypatch):
    import app.routes.agenda as agenda_module

    monkeypatch.setattr(agenda_module, "buscar_agendamentos", lambda *a, **k: [])

    resp = cliente_logado.get("/api/agendamentos")
    dados = resp.get_json()

    assert resp.status_code == 200
    assert dados["agendamentos"] == []
    assert dados["total"] == 0


def test_listar_agendamentos_com_falha_na_api(cliente_logado, monkeypatch):
    import app.routes.agenda as agenda_module

    def _levanta_erro(*args, **kwargs):
        raise AgendamentosAPIError("O serviço de agendamentos está indisponível no momento.")

    monkeypatch.setattr(agenda_module, "buscar_agendamentos", _levanta_erro)

    resp = cliente_logado.get("/api/agendamentos")
    dados = resp.get_json()

    assert resp.status_code == 502
    assert "indisponível" in dados["erro"]


def test_busca_paciente_inexistente_retorna_lista_vazia(cliente_logado, monkeypatch):
    import app.routes.agenda as agenda_module

    agendamentos_fake = [
        {
            "paciente": "Maria Oliveira",
            "cpf": "111.111.111-11",
            "medico": "Dr. João",
            "especialidade": "Cardiologia",
            "data": "2026-08-01",
            "horario": "09:00",
            "convenio": "Unimed",
            "status": "Confirmado",
        }
    ]
    monkeypatch.setattr(
        agenda_module, "buscar_agendamentos", lambda *a, **k: agendamentos_fake
    )

    resp = cliente_logado.get("/api/agendamentos?busca=PacienteQueNaoExiste")
    dados = resp.get_json()

    assert resp.status_code == 200
    assert dados["agendamentos"] == []


def test_acesso_sem_login_e_bloqueado(client):
    resp = client.get("/api/agendamentos")
    assert resp.status_code == 302
