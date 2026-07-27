# Agenda Médica

Aplicação web para login e consulta de agendamentos médicos, desenvolvida como
desafio técnico do processo seletivo da TimeSaver.

## Descrição da solução

Após autenticação, o usuário acessa uma tela que consulta agendamentos médicos
em uma API HTTP (mockada), exibindo os resultados em uma tabela interativa
(Tabulator), com busca por paciente, CPF ou médico. A aplicação trata de forma
controlada cenários de falha (credenciais inválidas, API fora do ar, resposta
vazia/inválida, campos obrigatórios ausentes, erro de banco de dados), sempre
exibindo mensagens compreensíveis ao usuário e registrando logs para
diagnóstico.

## Tecnologias utilizadas

- **Python 3.12 + Flask** — aplicação web e API mockada
- **SQLite** — armazenamento de usuários (tabela `usuarios`)
- **Tabulator.js** (via CDN) — exibição, busca e paginação dos agendamentos
- **Requests** — consumo HTTP da API de agendamentos, com retry/backoff
- **Docker / docker-compose** — orquestração da aplicação e da API mockada
- **Pytest + pytest-cov** — testes automatizados e cobertura
- **GitHub Actions** — CI rodando a suíte de testes a cada push/PR

## Arquitetura

```
agenda-medica/
├── app/                     # Aplicação principal (Flask)
│   ├── config.py            # Configurações via variáveis de ambiente
│   ├── models/               # Acesso a dados (SQLite) e regras de usuário
│   ├── routes/                # Blueprints: auth (login) e agenda (listagem)
│   ├── services/              # Cliente HTTP da API de agendamentos
│   ├── templates/             # login.html, agenda.html (Tabulator), erro.html
│   └── static/style.css
├── mock_api/                 # Serviço HTTP separado que simula a API de agendamentos
├── tests/                     # Testes automatizados (pytest)
├── seed.py                    # Script de criação do usuário de teste
├── run.py                     # Ponto de entrada da aplicação principal
├── Dockerfile / docker-compose.yml
└── requirements*.txt
```

A API de agendamentos foi implementada como um **serviço separado**
(`mock_api/`), simulando de forma mais realista uma integração externa real —
isso também exercita o cenário de "indisponibilidade da API" de forma
genuína (bastando parar o container `mock-api`).

## Deploy (Render)

Este repositório inclui um `render.yaml` (Render Blueprint) que sobe os dois
serviços — API mockada e aplicação principal — já conectados entre si:

1. Suba o repositório para o GitHub.
2. No [dashboard do Render](https://dashboard.render.com): **New +** →
   **Blueprint** → selecione o repositório.
3. O Render detecta o `render.yaml` e mostra os dois serviços para revisão
   → clique em **Apply**.
4. Aguarde o build de ambos os serviços. A URL pública da aplicação
   principal (`agenda-medica-web`) é a que você compartilha para acesso.

Credenciais de teste já configuradas via Blueprint: `teste@timesaver.com.br`
/ `senha123`.

> **Nota:** o plano free do Render "dorme" após ~15 min sem uso; o primeiro
> acesso após esse período pode levar 30-50s para responder (cold start dos
> dois serviços). O disco é efêmero no plano free — o SQLite é recriado a
> cada novo deploy, mas o `seed.py` roda automaticamente no start do
> container, então o usuário de teste sempre existe.

## Como executar com Docker (localmente)

Pré-requisitos: Docker e Docker Compose instalados.

```bash
# na raiz do projeto
docker compose up --build
```

Isso sobe dois serviços com um único comando:
- `mock-api` na porta **5001** (API de agendamentos)
- `web` na porta **5000** (aplicação principal, que também roda o seed do
  banco de usuários automaticamente antes de iniciar)

Acesse: http://localhost:5000

Para parar: `docker compose down` (use `docker compose down -v` para também
apagar o volume do banco SQLite).

### Variáveis de ambiente

Veja `.env.example`. Ao usar `docker compose up`, o Compose já lê um arquivo
`.env` na raiz do projeto automaticamente, se ele existir (copie de
`.env.example`). As credenciais do usuário de teste podem ser customizadas
por lá (`TEST_USER_EMAIL` / `TEST_USER_PASSWORD`).

## Como executar sem Docker (opcional)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Em um terminal: sobe a API mockada
python mock_api/app.py

# Em outro terminal: prepara o banco e sobe a aplicação principal
python seed.py
python run.py
```

## Credenciais do usuário de teste

- **E-mail:** `teste@timesaver.com.br`
- **Senha:** `senha123`

(Criadas automaticamente pelo `seed.py` / pelo entrypoint do container `web`.)

## Exemplos de uso

1. Acesse `http://localhost:5000` → redirecionado para `/login`.
2. Informe as credenciais de teste acima.
3. Após o login, a tela de agenda carrega automaticamente os agendamentos
   vindos da API, exibidos em uma tabela com colunas: data, horário,
   paciente, CPF, médico, especialidade, convênio e status.
4. Digite no campo de busca um nome, CPF ou médico para filtrar os
   resultados em tempo real. Se não houver correspondência, a tabela exibe
   "Nenhum agendamento encontrado."
5. Para simular a API fora do ar, pare o container/processo `mock-api` e
   atualize a página de agenda — a aplicação exibirá uma mensagem amigável
   em vez de quebrar.

## Testes automatizados

```bash
pip install -r requirements-dev.txt
pytest -v

# com relatório de cobertura
pytest --cov=app --cov-report=term-missing
```

Cobertura atual: **~86%** (medida com `pytest-cov`). Rodado automaticamente
a cada push/PR via GitHub Actions (`.github/workflows/testes.yml`).

Cenários cobertos:
- login com credenciais válidas e inválidas, e campos vazios
- bloqueio por excesso de tentativas (força bruta) e proteção CSRF
- política mínima de senha na criação de usuário
- bloqueio de acesso à agenda/API sem sessão ativa
- listagem de agendamentos sem resultados
- falha da API de agendamentos (erro tratado, resposta 502 com mensagem
  amigável) e recuperação automática via retry após falha transitória
- busca por paciente inexistente
- cliente HTTP: timeout, conexão recusada, erro 4xx (sem retry), resposta
  vazia, JSON inválido, CPF em formato inválido e campos obrigatórios
  ausentes

## Decisões técnicas

- **API como serviço separado**: optei por um serviço Flask independente em
  vez de um endpoint mockado dentro da própria aplicação, para simular de
  forma mais fiel uma integração real com um sistema externo (inclusive nos
  cenários de falha).
- **Descarte silencioso de registros incompletos**: em vez de rejeitar a
  resposta inteira da API quando um único agendamento vem com campo
  obrigatório ausente (ou CPF malformado), o registro problemático é
  descartado e um aviso é registrado em log — a aplicação segue funcionando
  com os dados válidos restantes.
- **Retry com backoff exponencial**: falhas transitórias (timeout, conexão
  recusada, erro 5xx) são reprocessadas automaticamente até 3 vezes antes
  de reportar erro ao usuário. Erros 4xx não são reprocessados, pois
  repetir a mesma requisição não mudaria o resultado.
- **Sessão simples via Flask `session`** (cookie assinado) para autenticação,
  suficiente para o escopo do desafio; em um cenário de produção real,
  avaliaria JWT ou Flask-Login com expiração/refresh.
- **Busca no back-end**: o filtro por paciente/CPF/médico é feito no
  servidor (`/api/agendamentos?busca=...`), reaproveitado tanto para o
  carregamento inicial quanto para a busca dinâmica do Tabulator.
- **Verificação da API ao iniciar pelo terminal**: `run.py` faz uma consulta
  inicial à API de agendamentos ao subir e registra o resultado no log,
  atendendo ao requisito de a aplicação "entregar os dados quando iniciada
  pelo terminal" sem bloquear a subida do servidor caso a API esteja
  temporariamente indisponível.
- **CSRF com token sincronizado (sem dependência externa)**: implementação
  própria (`app/security.py`) em vez de Flask-WTF, para manter as
  dependências do projeto enxutas — a técnica (synchronizer token pattern)
  é a mesma usada por bibliotecas prontas.

## Segurança

- Senhas armazenadas com hash (`werkzeug.security`, PBKDF2), com política
  mínima na criação (8+ caracteres, ao menos uma letra e um número).
- Proteção **CSRF** nos formulários de login/logout (synchronizer token
  pattern, próprio, sem dependência externa).
- Cookies de sessão com `HttpOnly` e `SameSite=Lax`; `Secure` habilitável via
  `SESSION_COOKIE_SECURE=1` (usar sempre atrás de HTTPS em produção).
- Bloqueio temporário após 5 tentativas de login inválidas por combinação
  IP + e-mail, em janela de 5 minutos (proteção simples contra força bruta;
  implementação em memória, válida para uma única instância — ver
  "Próximos passos").
- Consultas ao SQLite sempre parametrizadas (sem concatenação de SQL).
- Cabeçalhos HTTP básicos de segurança (`X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`) aplicados a todas as respostas.
- `SECRET_KEY` alerta em log e usa um valor aleatório por processo caso não
  seja definida via variável de ambiente, evitando o uso silencioso de uma
  chave padrão previsível.
- Containers Docker rodam com usuário não-root.

## Observabilidade

- **Healthcheck** em `/health` (aplicação principal) e `/health` (API
  mockada), verificando inclusive a conectividade com o banco de dados —
  útil para load balancers e para o monitoramento automático do Render.
- **Logs estruturados em JSON**, ativáveis via `LOG_FORMAT=json` (formato
  texto simples é o padrão, mais legível em desenvolvimento local). Facilita
  integração futura com ferramentas como Datadog, ELK ou CloudWatch Logs
  Insights.

## Limitações conhecidas

- O bloqueio de tentativas de login (força bruta) é em memória do processo;
  em um deploy com múltiplas réplicas, precisaria de um armazenamento
  compartilhado (ex.: Redis) para funcionar corretamente entre instâncias.
- A tabela `agendamentos_cache` existe no schema para uso futuro (ex.: cache
  local dos dados da API), mas não é utilizada nesta versão — os dados são
  buscados diretamente da API a cada requisição.
- A paginação da tabela (Tabulator) é feita inteiramente no front-end; para
  um volume de dados muito maior, seria necessário paginar também a
  consulta no back-end/API.

## Próximos passos (fora do escopo deste desafio)

Itens que dependem de infraestrutura externa não disponível no ambiente
deste desafio, mas que eu levaria em conta evoluindo o projeto para
produção:

- **PostgreSQL** no lugar do SQLite — SQLite serializa escritas (um único
  writer por vez), o que não escala para uso multiusuário real.
- **Migrations com Alembic** no lugar do `seed.py` manual — versionamento
  de schema com rollback.
- **Cache dos agendamentos (Redis)** com TTL curto — reduz carga na API
  externa e melhora tempo de resposta.
- **Rate limiting e circuit breaker distribuídos (Redis)** — a proteção
  contra força bruta e o retry atuais funcionam por instância; em múltiplas
  réplicas precisariam de estado compartilhado.
- **Métricas** (tempo de resposta, taxa de erro por endpoint) exportadas
  para Prometheus/Datadog.
- **Validação de schema com Pydantic** na resposta da API de agendamentos,
  no lugar da checagem manual de campos atual.
