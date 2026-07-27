def test_login_valido_redireciona_para_agenda(client):
    resp = client.post(
        "/login",
        data={"email": "teste@timesaver.com.br", "senha": "senha123"},
    )
    assert resp.status_code == 302
    assert "/agenda" in resp.headers["Location"]


def test_login_invalido_retorna_mensagem_de_erro(client):
    resp = client.post(
        "/login",
        data={"email": "teste@timesaver.com.br", "senha": "senha-errada"},
    )
    assert resp.status_code == 401
    assert "invál" in resp.get_data(as_text=True).lower()


def test_login_com_campos_vazios_nao_quebra(client):
    resp = client.post("/login", data={"email": "", "senha": ""})
    assert resp.status_code == 400


def test_acesso_agenda_sem_login_redireciona(client):
    resp = client.get("/agenda")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_bloqueio_apos_varias_tentativas_invalidas(client):
    import app.routes.auth as auth_module

    auth_module._tentativas_login.clear()

    for _ in range(5):
        client.post(
            "/login",
            data={"email": "teste@timesaver.com.br", "senha": "senha-errada"},
        )

    resp = client.post(
        "/login",
        data={"email": "teste@timesaver.com.br", "senha": "senha-errada"},
    )
    assert resp.status_code == 429
    assert "muitas tentativas" in resp.get_data(as_text=True).lower()

    auth_module._tentativas_login.clear()
