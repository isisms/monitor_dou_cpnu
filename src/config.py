from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
INLABS_EMAIL = os.getenv("INLABS_EMAIL")
INLABS_SENHA = os.getenv("INLABS_SENHA")
BROWSER_CHANNEL = os.getenv("BROWSER_CHANNEL", "msedge")