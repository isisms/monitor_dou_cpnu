import requests
import urllib3
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def enviar_mensagem_telegram(texto: str) -> dict:
    url = f"https://api.telegram.org/bot8798585588:AAFIxnvRmyN_HFyJiHmna37TYHQ0FMwNokg/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto
    }

    resposta = requests.post(
        url,
        data=payload,
        timeout=30,
        verify=False
    )

    resposta.raise_for_status()
    return resposta.json()