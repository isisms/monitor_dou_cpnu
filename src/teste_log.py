import pandas as pd
from exportacao import salvar_log

df = pd.DataFrame([
    {
        "data_coleta": "2026-03-08",
        "hora_coleta": "16:00",
        "termo": "ATDS",
        "titulo": "Teste de registro",
        "link": "https://exemplo.com",
        "fonte": "teste",
        "alerta_enviado": "sim"
    }
])

salvar_log(df)
print("Log salvo com sucesso.")