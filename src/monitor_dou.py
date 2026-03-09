from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

from coletor_dou_portal import coletar_materias_dou, TERMOS_BUSCA
from alerta_telegram import enviar_mensagem_telegram


BASE_DIR = Path(__file__).resolve().parent.parent
CAMINHO_HISTORICO = BASE_DIR / "output" / "planilhas" / "historico_monitoramento_dou.xlsx"
CAMINHO_NOVIDADES = BASE_DIR / "output" / "planilhas" / "novidades_dou.xlsx"


def carregar_historico() -> pd.DataFrame:
    if CAMINHO_HISTORICO.exists():
        return pd.read_excel(CAMINHO_HISTORICO)
    return pd.DataFrame()


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    df = df.copy()
    agora = datetime.now()
    df["data_coleta"] = agora.strftime("%d/%m/%Y")
    df["hora_coleta"] = agora.strftime("%H:%M:%S")
    df["alerta_enviado"] = "NAO"
    return df


def identificar_novidades(df_novo: pd.DataFrame, df_historico: pd.DataFrame) -> pd.DataFrame:
    if df_novo.empty:
        return df_novo.copy()

    if df_historico.empty or "link" not in df_historico.columns:
        return df_novo.copy()

    links_historico = set(df_historico["link"].dropna().astype(str).unique())
    df_novidades = df_novo[~df_novo["link"].astype(str).isin(links_historico)].copy()
    return df_novidades


def salvar_historico(df_historico: pd.DataFrame, df_novidades: pd.DataFrame) -> pd.DataFrame:
    if df_historico.empty:
        df_final = df_novidades.copy()
    else:
        df_final = pd.concat([df_historico, df_novidades], ignore_index=True)

    if not df_final.empty:
        df_final = df_final.drop_duplicates(subset=["link"]).reset_index(drop=True)

    CAMINHO_HISTORICO.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_excel(CAMINHO_HISTORICO, index=False)
    return df_final


def salvar_novidades(df_novidades: pd.DataFrame) -> None:
    CAMINHO_NOVIDADES.parent.mkdir(parents=True, exist_ok=True)
    df_novidades.to_excel(CAMINHO_NOVIDADES, index=False)


def montar_resumo_telegram(df_novidades: pd.DataFrame) -> str:
    if df_novidades.empty:
        return "Monitor DOU: nenhuma novidade encontrada."

    total = len(df_novidades)
    altas = (df_novidades["prioridade"] == "ALTA").sum() if "prioridade" in df_novidades.columns else 0
    medias = (df_novidades["prioridade"] == "MEDIA").sum() if "prioridade" in df_novidades.columns else 0
    baixas = (df_novidades["prioridade"] == "BAIXA").sum() if "prioridade" in df_novidades.columns else 0

    linhas = [
        "Monitor DOU",
        f"Novidades enviadas no alerta: {total}",
        f"Alta prioridade: {altas}",
        f"Média prioridade: {medias}",
        f"Baixa prioridade: {baixas}",
        "",
    ]

    # ordenação manual de prioridade
    mapa_prioridade = {"ALTA": 1, "MEDIA": 2, "BAIXA": 3}
    df_tmp = df_novidades.copy()
    df_tmp["ordem_prioridade"] = df_tmp["prioridade"].map(mapa_prioridade).fillna(99)

    top = df_tmp.sort_values(
        by=["ordem_prioridade", "data_publicacao", "titulo"],
        ascending=[True, False, True]
    ).head(5)

    for i, (_, row) in enumerate(top.iterrows(), start=1):
        titulo = str(row.get("titulo", ""))[:180]
        data_pub = str(row.get("data_publicacao", ""))
        categoria = str(row.get("categoria", ""))
        prioridade = str(row.get("prioridade", ""))
        tipo_ato = str(row.get("tipo_ato", ""))
        link = str(row.get("link", ""))

        linhas.append(f"{i}. [{prioridade}] [{categoria}] [{tipo_ato}] {data_pub}")
        linhas.append(titulo)
        linhas.append(link)
        linhas.append("")

    return "\n".join(linhas).strip()


def marcar_alerta_enviado(df_novidades: pd.DataFrame) -> pd.DataFrame:
    if df_novidades.empty:
        return df_novidades.copy()

    df_novidades = df_novidades.copy()
    df_novidades["alerta_enviado"] = "SIM"
    return df_novidades


if __name__ == "__main__":
    print("Iniciando monitoramento do DOU...")
    df_coleta = coletar_materias_dou(TERMOS_BUSCA)

    if df_coleta.empty:
        print("Nenhum registro coletado.")
    else:
        # mantém apenas o que foi classificado como relevante
        df_coleta = df_coleta[df_coleta["categoria"] != "OUTRO"].copy()
        df_coleta = preparar_dataframe(df_coleta)

        df_historico = carregar_historico()
        df_novidades = identificar_novidades(df_coleta, df_historico)

        print(f"Total coletado nesta rodada: {len(df_coleta)}")
        print(f"Novidades encontradas: {len(df_novidades)}")

        if not df_novidades.empty:
            # recorte apenas para o alerta do Telegram
            df_alerta = df_novidades[
                df_novidades["prioridade"].isin(["ALTA", "MEDIA"])
            ].copy()

            print(f"Novidades que entram no alerta: {len(df_alerta)}")

            if not df_alerta.empty:
                mensagem = montar_resumo_telegram(df_alerta)
                enviar_mensagem_telegram(mensagem)
                print("Mensagem enviada no Telegram.")
            else:
                print("Houve novidades, mas nenhuma de prioridade ALTA ou MEDIA.")

            # marca todas as novidades como processadas no histórico
            df_novidades = marcar_alerta_enviado(df_novidades)

        salvar_novidades(df_novidades)
        df_final = salvar_historico(df_historico, df_novidades)

        print(f"Histórico total após atualização: {len(df_final)}")
        print(f"Arquivo de histórico: {CAMINHO_HISTORICO}")
        print(f"Arquivo de novidades: {CAMINHO_NOVIDADES}")