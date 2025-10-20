import os
import sys
from pathlib import Path

# Asegurar import de src
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT.parent))  # para 'src.*'

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

MODE = os.getenv("START_MODE", os.environ.get("START_MODE", "server")).lower()

if MODE == "polling":
    # Ejecutar Telegram polling
    import subprocess
    subprocess.run([sys.executable, "src/connectors/telegram_polling.py"], check=True)
elif MODE == "discord":
    # Ejecutar conector Discord (Gateway)
    import subprocess
    subprocess.run([sys.executable, "src/connectors/discord_connector.py"], check=True)
else:
    # Ejecutar API FastAPI
    import uvicorn
    uvicorn.run("src.app.server:app", host="0.0.0.0", port=8001)
