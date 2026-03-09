from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    INLABS_EMAIL,
    INLABS_SENHA,
    BROWSER_CHANNEL,
)

print("Token Telegram carregado:", bool(TELEGRAM_BOT_TOKEN))
print("Chat ID carregado:", bool(TELEGRAM_CHAT_ID))
print("Email INLABS carregado:", bool(INLABS_EMAIL))
print("Senha INLABS carregada:", bool(INLABS_SENHA))
print("Canal do navegador:", BROWSER_CHANNEL)