from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CAMINHO_LOG = BASE_DIR / "output" / "planilhas" / "log_monitoramento.xlsx"

def salvar_log(df: pd.DataFrame) -> None:
    CAMINHO_LOG.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(CAMINHO_LOG, index=False)