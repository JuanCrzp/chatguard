# logging.py - Logging funcional para Bot Comunidad
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

logger = logging.getLogger("bot_comunidad")

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)


def log_event(event: str, **kwargs):
    """Log estructurado JSON de eventos informativos."""
    try:
        payload = {"event": event, **kwargs}
        logger.info(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.info(f"{event} | {kwargs} | json_error={e}")


def log_error_event(event: str, **kwargs):
    """Log estructurado JSON para errores."""
    try:
        payload = {"event": event, **kwargs}
        logger.error(json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.error(f"{event} | {kwargs} | json_error={e}")
