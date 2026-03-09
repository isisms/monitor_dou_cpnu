import requests
import urllib3
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = f"https://api.telegram.org/bot8798585588:AAFIxnvRmyN_HFyJiHmna37TYHQ0FMwNokg/sendMessage"

payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "Teste do monitor DOU: conexão com Telegram funcionando."
}

resposta = requests.post(url, data=payload, timeout=30, verify=False)

print("Status code:", resposta.status_code)
print("Resposta:", resposta.text)