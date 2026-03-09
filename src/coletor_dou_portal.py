from __future__ import annotations
from config import BROWSER_CHANNEL
import os
from pathlib import Path
from urllib.parse import quote_plus
import re
import time
import unicodedata

import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "output" / "planilhas" / "coleta_dou_portal_v2.xlsx"

TERMOS_BUSCA = [
    "CPNU 2",
    "CPNU",
    "Concurso Público Nacional Unificado",
    "Analista Técnico de Desenvolvimento Socioeconômico",
    "ATDS",
]

BROWSER_CHANNEL = "msedge"

TERMOS_CPNU = [
    "cpnu",
    "concurso publico nacional unificado",
    "concurso nacional unificado",
]

TERMOS_ATDS = [
    "atds",
    "analista tecnico de desenvolvimento socioeconomico",
    "carreira de desenvolvimento socioeconomico",
]


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto


def limpar_texto(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def montar_url_busca(termo: str) -> str:
    termo_codificado = quote_plus(f'"{termo}"')
    return f"https://www.in.gov.br/search?q={termo_codificado}"


def extrair_links_dou_do_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if "/web/dou/-/" in href:
            if href.startswith("/"):
                href = f"https://www.in.gov.br{href}"
            elif href.startswith("http"):
                href = href
            else:
                href = f"https://www.in.gov.br/{href.lstrip('/')}"
            links.append(href)

    return list(dict.fromkeys(links))


def extrair_titulo_real(soup: BeautifulSoup) -> str:
    meta_og = soup.find("meta", attrs={"property": "og:title"})
    if meta_og and meta_og.get("content"):
        titulo = limpar_texto(meta_og["content"])
    else:
        titulo = ""

    if not titulo:
        meta_name = soup.find("meta", attrs={"name": "title"})
        if meta_name and meta_name.get("content"):
            titulo = limpar_texto(meta_name["content"])

    if not titulo:
        for tag in soup.find_all(["h1", "h2"]):
            txt = limpar_texto(tag.get_text(" ", strip=True))
            if txt and txt.lower() != "imprensa nacional":
                titulo = txt
                break

    # limpeza final do sufixo do portal
    titulo = re.sub(r"\s*-\s*DOU\s*-\s*Imprensa Nacional\s*$", "", titulo, flags=re.IGNORECASE)
    titulo = re.sub(r"\s{2,}", " ", titulo).strip()

    return titulo

def extrair_corpo_util(texto_completo: str, titulo: str) -> str:
    texto = texto_completo

    # corta tudo antes de "Publicado em:"
    if "Publicado em:" in texto:
        texto = texto.split("Publicado em:", 1)[1]
        texto = "Publicado em:" + texto

    # corta tudo antes do órgão, se existir
    if "Órgão:" in texto:
        texto = texto.split("Órgão:", 1)[1]
        texto = "Órgão:" + texto

    # remove excesso de cabeçalhos repetidos
    lixo_inicio = [
        "Você precisa habilitar o JavaScript",
        "Ir para o conteúdo",
        "Ir para o rodapé",
        "Acesso rápido",
        "Órgãos do Governo",
        "Acesso à Informação",
        "Legislação",
        "Acessibilidade",
        "Portal da Imprensa Nacional",
        "Caminho de Navegação",
        "Diário Oficial da União",
        "Publicador de Conteúdos e Mídias",
        "Voltar",
        "Compartilhe:",
        "Imagem não disponível",
        "Compartilhar",
        "Ícone Versão certificada",
        "Ícone Diário Completo",
        "Ícone Impressão",
        "Brasão do Brasil",
    ]

    for item in lixo_inicio:
        texto = texto.replace(item, " ")

    # remove repetições do título no começo
    if titulo:
        texto = texto.replace(f"{titulo} - {titulo}", titulo)
        texto = texto.replace(f"{titulo} {titulo}", titulo)

    texto = re.sub(r"https?://\S+", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto[:3000]

def identificar_tipo_ato(titulo: str, trecho: str) -> str:
    texto = normalizar_texto(f"{titulo} {trecho}")

    if "edital" in texto:
        return "EDITAL"
    if "portaria" in texto:
        return "PORTARIA"
    if "decreto" in texto:
        return "DECRETO"
    if "extrato" in texto:
        return "EXTRATO"
    if "despacho" in texto:
        return "DESPACHO"
    if "resolucao" in texto:
        return "RESOLUCAO"
    return "OUTRO"


def identificar_prioridade(titulo: str, trecho: str, categoria: str) -> str:
    texto = normalizar_texto(f"{titulo} {trecho}")

    termos_alta = [
        "convocacao",
        "confirmacao de interesse",
        "nomeacao",
        "homologacao",
        "resultado final",
        "resultado",
        "edital especifico",
        "cadastro reserva",
        "lista de espera",
        "provimento",
    ]

    termos_media = [
        "edital",
        "retificacao",
        "cronograma",
        "prova",
        "gabarito",
        "curso de formacao",
    ]

    if categoria == "CPNU_ATDS":
        return "ALTA"

    if any(t in texto for t in termos_alta):
        return "ALTA"

    if any(t in texto for t in termos_media):
        return "MEDIA"

    return "BAIXA"

from datetime import datetime


def marcar_publicado_hoje(data_publicacao: str) -> str:
    if not data_publicacao:
        return "NAO"

    try:
        data_pub = datetime.strptime(data_publicacao, "%d/%m/%Y").date()
        hoje = datetime.today().date()
        return "SIM" if data_pub == hoje else "NAO"
    except Exception:
        return "NAO"

def classificar_relevancia(titulo: str, trecho: str) -> str:
    texto = normalizar_texto(f"{titulo} {trecho}")

    tem_cpnu = any(t in texto for t in TERMOS_CPNU)
    tem_atds = any(t in texto for t in TERMOS_ATDS)

    if tem_cpnu and tem_atds:
        return "CPNU_ATDS"
    if tem_cpnu:
        return "CPNU"
    if tem_atds:
        return "ATDS"
    return "OUTRO"


def extrair_metadados_materia(html: str, link: str, termo: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    texto_completo = soup.get_text("\n", strip=True)

    titulo = extrair_titulo_real(soup)

    publicado_em = ""
    edicao = ""
    secao = ""
    pagina = ""
    orgao = ""

    m_pub = re.search(
        r"Publicado em:\s*([0-9]{2}/[0-9]{2}/[0-9]{4})\s*\|\s*Edição:\s*([^|]+)\|\s*Seção:\s*([^|]+)\|\s*Página:\s*(.+)",
        texto_completo
    )
    if m_pub:
        publicado_em = limpar_texto(m_pub.group(1))
        edicao = limpar_texto(m_pub.group(2))
        secao = limpar_texto(m_pub.group(3))
        pagina = limpar_texto(m_pub.group(4).split("Órgão:")[0])

    m_orgao = re.search(r"Órgão:\s*(.+?)\s*(?:EDITAL|PORTARIA|RESOLUÇÃO|EXTRATO|DESPACHO|INSTRUÇÃO|$)", texto_completo)
    if m_orgao:
        orgao = limpar_texto(m_orgao.group(1))

    if not orgao:
        linhas = [limpar_texto(x) for x in texto_completo.split("\n") if limpar_texto(x)]
        for i, linha in enumerate(linhas):
            if linha.startswith("Órgão:"):
                orgao = limpar_texto(linha.replace("Órgão:", "", 1))
                if not orgao and i + 1 < len(linhas):
                    orgao = linhas[i + 1]
                break

    trecho = extrair_corpo_util(texto_completo, titulo)
    categoria = classificar_relevancia(titulo, trecho)
    tipo_ato = identificar_tipo_ato(titulo, trecho)
    prioridade = identificar_prioridade(titulo, trecho, categoria)
    publicado_hoje = marcar_publicado_hoje(publicado_em)

    return {
        "termo_busca": termo,
        "categoria": categoria,
        "prioridade": prioridade,
        "tipo_ato": tipo_ato,
        "publicado_hoje": publicado_hoje,
        "titulo": titulo,
        "data_publicacao": publicado_em,
        "edicao": edicao,
        "secao": secao,
        "pagina": pagina,
        "orgao": orgao,
        "link": link,
        "trecho_texto": trecho,
    }


def coletar_links_por_termo(page, termo: str, pausa: float = 2.0) -> list[str]:
    url = montar_url_busca(termo)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(pausa)

    html = page.content()
    links = extrair_links_dou_do_html(html)
    return links

def abrir_navegador(playwright):
    # GitHub Actions define a variável GITHUB_ACTIONS=true
    em_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    if em_github_actions:
        return playwright.chromium.launch(headless=True)

    if BROWSER_CHANNEL:
        return playwright.chromium.launch(channel=BROWSER_CHANNEL, headless=True)

    return playwright.chromium.launch(headless=True)


def coletar_materias_dou(termos: list[str]) -> pd.DataFrame:
    registros = []

    with sync_playwright() as p:
        browser = abrir_navegador(p)
        page = browser.new_page()

        for termo in termos:
            print(f"Buscando termo: {termo}")
            links = coletar_links_por_termo(page, termo)
            print(f"  Links encontrados: {len(links)}")

            for link in links:
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(1.5)
                    html_materia = page.content()

                    registro = extrair_metadados_materia(
                        html=html_materia,
                        link=link,
                        termo=termo,
                    )
                    registros.append(registro)

                except Exception as e:
                    registros.append({
                        "termo_busca": termo,
                        "categoria": "ERRO",
                        "titulo": "",
                        "data_publicacao": "",
                        "edicao": "",
                        "secao": "",
                        "pagina": "",
                        "orgao": "",
                        "link": link,
                        "trecho_texto": f"ERRO NA COLETA DA MATÉRIA: {e}",
                    })

        browser.close()

    df = pd.DataFrame(registros)

    if not df.empty:
        df = df.drop_duplicates(subset=["link"]).reset_index(drop=True)

    return df


def salvar_resultado(df: pd.DataFrame) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT_PATH, index=False)
    print(f"Arquivo salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    df_resultado = coletar_materias_dou(TERMOS_BUSCA)

    if not df_resultado.empty:
        print("\nResumo por categoria:")
        print(df_resultado["categoria"].value_counts(dropna=False))

        print("\nResumo por prioridade:")
        print(df_resultado["prioridade"].value_counts(dropna=False))

        df_filtrado = df_resultado[df_resultado["categoria"] != "OUTRO"].copy()

        colunas_ordem = [
            "termo_busca",
            "categoria",
            "prioridade",
            "tipo_ato",
            "publicado_hoje",
            "titulo",
            "data_publicacao",
            "edicao",
            "secao",
            "pagina",
            "orgao",
            "link",
            "trecho_texto",
        ]
        df_filtrado = df_filtrado[colunas_ordem]
    else:
        df_filtrado = df_resultado.copy()

    print("\nAmostra final:")
    print(df_filtrado.head())

    salvar_resultado(df_filtrado)
