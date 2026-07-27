"""API mockada de agendamentos médicos.

Serviço Flask simples e independente, que simula o sistema de agendamentos
da clínica. Pode ser iniciado separadamente pelo terminal:

    python mock_api/app.py

Endpoints:
    GET /api/agendamentos          -> lista completa de agendamentos
    GET /health                    -> healthcheck simples
"""
import logging
import os

from flask import Flask, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

AGENDAMENTOS_MOCK = [
    {
        "paciente": "Maria Oliveira Santos",
        "cpf": "123.456.789-00",
        "medico": "Dr. Carlos Andrade",
        "especialidade": "Cardiologia",
        "data": "2026-07-28",
        "horario": "09:00",
        "convenio": "Unimed",
        "status": "Confirmado",
    },
    {
        "paciente": "João Pedro Lima",
        "cpf": "987.654.321-00",
        "medico": "Dra. Fernanda Souza",
        "especialidade": "Dermatologia",
        "data": "2026-07-28",
        "horario": "10:30",
        "convenio": "Bradesco Saúde",
        "status": "Aguardando confirmação",
    },
    {
        "paciente": "Ana Beatriz Costa",
        "cpf": "111.222.333-44",
        "medico": "Dr. Carlos Andrade",
        "especialidade": "Cardiologia",
        "data": "2026-07-29",
        "horario": "14:00",
        "convenio": "Particular",
        "status": "Confirmado",
    },
    {
        "paciente": "Rafael Nascimento",
        "cpf": "555.666.777-88",
        "medico": "Dra. Beatriz Rocha",
        "especialidade": "Ortopedia",
        "data": "2026-07-30",
        "horario": "08:15",
        "convenio": "SulAmérica",
        "status": "Cancelado",
    },
    {
        "paciente": "Larissa Fernandes",
        "cpf": "222.333.444-55",
        "medico": "Dra. Fernanda Souza",
        "especialidade": "Dermatologia",
        "data": "2026-07-30",
        "horario": "16:45",
        "convenio": "Amil",
        "status": "Confirmado",
    },
]


@app.route("/api/agendamentos", methods=["GET"])
def listar_agendamentos():
    logger.info("Entregando %d agendamento(s).", len(AGENDAMENTOS_MOCK))
    return jsonify(AGENDAMENTOS_MOCK)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", os.environ.get("MOCK_API_PORT", "5001")))
    logger.info("Iniciando API mockada de agendamentos na porta %d...", porta)
    logger.info("Dados disponíveis: %d agendamento(s) cadastrados.", len(AGENDAMENTOS_MOCK))
    app.run(host="0.0.0.0", port=porta)
