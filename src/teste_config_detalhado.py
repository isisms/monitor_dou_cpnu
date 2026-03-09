from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("Token existe:", bool(TELEGRAM_BOT_TOKEN))
print("Chat ID existe:", bool(TELEGRAM_CHAT_ID))

if TELEGRAM_BOT_TOKEN:
    print("Início do token:", TELEGRAM_BOT_TOKEN[:12])

if TELEGRAM_CHAT_ID:
    print("Chat ID:", TELEGRAM_CHAT_ID)