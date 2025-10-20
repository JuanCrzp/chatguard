# config.py - Configuración centralizada para Bot Comunidad
import os
from urllib.parse import quote_plus as _urlquote

BOT_ENV = os.getenv("BOT_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

# Variables MySQL (preferencia por variables separadas; fallback a DB_URL)
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Si se proveen variables separadas, componer URL estilo SQLAlchemy con pymysql
_composed_db_url = None
if all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
	# Percent-encode usuario, contraseña y nombre de base para soportar caracteres especiales/no ASCII
	user_enc = _urlquote(DB_USER, safe="")
	pass_enc = _urlquote(DB_PASSWORD, safe="")
	dbname_enc = _urlquote(DB_NAME, safe="")
	_composed_db_url = (
		f"mysql+pymysql://{user_enc}:{pass_enc}@{DB_HOST}:{DB_PORT}/{dbname_enc}?charset=utf8mb4"
	)

# Compatibilidad: si no hay variables separadas, usar DB_URL existente
DB_URL = _composed_db_url or os.getenv(
	"DB_URL",
	"mysql+pymysql://user:pass@localhost:3306/bot_comunidad?charset=utf8mb4",
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")

# Envío automático a plataformas desde el webhook
SEND_AUTOMATIC_RESPONSES = os.getenv("SEND_AUTOMATIC_RESPONSES", "true").lower() in ("1", "true", "yes")
