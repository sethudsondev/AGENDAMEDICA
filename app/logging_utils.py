import json
import logging


class JsonFormatter(logging.Formatter):
    """Formata cada linha de log como um objeto JSON, facilitando a
    ingestão por ferramentas de observabilidade (ex.: Datadog, ELK,
    CloudWatch Logs Insights).

    Ativado via variável de ambiente LOG_FORMAT=json. O formato padrão
    (texto simples) é mantido como default para facilitar a leitura
    durante o desenvolvimento local.
    """

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)
