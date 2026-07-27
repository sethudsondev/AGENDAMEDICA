import pytest


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


def test_csrf_bloqueia_post_sem_token_fora_do_modo_de_teste(app, client):
    """O bypass de CSRF só vale com TESTING=True; aqui desligamos
    temporariamente para confirmar que a proteção funciona de verdade."""
    app.testing = False
    try:
        resp = client.post(
            "/login",
            data={"email": "teste@timesaver.com.br", "senha": "senha123"},
        )
        assert resp.status_code == 400
    finally:
        app.testing = True


def test_politica_de_senha_rejeita_senha_curta():
    from app.models.usuario import criar_usuario, SenhaFracaError
    import tempfile
    import os

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        from app import create_app
        from app.config import Config

        class _Config(Config):
            DB_PATH = db_path

        create_app(_Config)  # garante que as tabelas existam

        with pytest.raises(SenhaFracaError):
            criar_usuario(db_path, "novo@teste.com", "123")
    finally:
        os.close(db_fd)
        os.unlink(db_path)
