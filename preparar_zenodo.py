"""Prepara versões agregadas das Bases 1 e 2 para depósito público no Zenodo.

Não exporta respostas individuais, nomes de perfis, URLs, títulos ou links
de publicações. Os arquivos são resumos agregados e não substituem as bases
originais utilizadas internamente para construir os grafos.
"""

from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SAIDA = ROOT / "outputs" / "zenodo"

ARQUIVO_BASE1 = DATA / "dados_originais.xlsx"
ARQUIVO_BASE2 = DATA / "Pasta(base_youtube_instagram).csv"

COLUNA_CANAIS = (
    "Qual foi a principal forma pela qual você teve contato "
    "com esse tipo de conteúdo?"
)

CANAIS = [
    "Instagram",
    "YouTube",
    "Influenciadores",
    "Amigos/conhecidos",
    "TikTok",
    "Sites esportivos",
    "Facebook",
    "Outro",
    "X/Twitter",
]

CORRECOES = {
    "Amingos/conhecidos": "Amigos/conhecidos",
    "SItes esportivos": "Sites esportivos",
}


def preparar_base1() -> None:
    """Gera frequências agregadas dos canais, sem linhas por participante."""
    if not ARQUIVO_BASE1.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_BASE1}")

    dados = pd.read_excel(ARQUIVO_BASE1)
    if COLUNA_CANAIS not in dados.columns:
        raise ValueError(f"Coluna esperada não encontrada: {COLUNA_CANAIS}")

    frequencias = {canal: 0 for canal in CANAIS}
    for resposta in dados[COLUNA_CANAIS].dropna():
        for item in str(resposta).split(","):
            canal = CORRECOES.get(item.strip(), item.strip())
            if canal in frequencias:
                frequencias[canal] += 1

    total_participantes = int(len(dados))
    resultado = pd.DataFrame([
        {
            "canal": canal,
            "participantes_que_mencionaram": quantidade,
            "percentual_dos_participantes": (
                round(100 * quantidade / total_participantes, 2)
                if total_participantes else 0
            ),
            "total_participantes_questionario": total_participantes,
        }
        for canal, quantidade in frequencias.items()
    ])
    resultado.to_csv(
        SAIDA / "base1_frequencia_canais.csv",
        index=False,
        encoding="utf-8-sig",
    )


def normalizar_rede(valor: str) -> str:
    valor = str(valor).strip()
    mapa = {
        "Youtube": "YouTube",
        "youtube": "YouTube",
        "instagram": "Instagram",
    }
    return mapa.get(valor, valor)


def normalizar_plataforma(valor: str) -> str:
    texto = str(valor).strip()
    if not texto or texto.casefold() in {
        "não identificada", "nao identificada",
        "não identificado", "nao identificado",
    }:
        return "Não identificada"
    return texto


def preparar_base2() -> None:
    """Gera contagens agregadas por rede e plataforma, sem perfis/publicações."""
    if not ARQUIVO_BASE2.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ARQUIVO_BASE2}")

    dados = None
    erro = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            dados = pd.read_csv(
                ARQUIVO_BASE2, sep=";", encoding=encoding, dtype=str
            )
            break
        except UnicodeDecodeError as exc:
            erro = exc
    if dados is None:
        raise UnicodeError("Não foi possível ler o CSV da Base 2.") from erro

    obrigatorias = {"ID", "Rede", "Casa de Aposta"}
    faltantes = obrigatorias.difference(dados.columns)
    if faltantes:
        raise ValueError(
            "Colunas ausentes na Base 2: " + ", ".join(sorted(faltantes))
        )

    dados["Rede"] = dados["Rede"].fillna("").map(normalizar_rede)
    dados["Casa de Aposta"] = (
        dados["Casa de Aposta"].fillna("").map(normalizar_plataforma)
    )

    # A saída contém somente totais por rede/plataforma. Nenhum identificador
    # de perfil, nome, URL, título, link ou descrição de publicação é exportado.
    resultado = (
        dados.groupby(["Rede", "Casa de Aposta"], dropna=False)
        .agg(
            quantidade_registros=("ID", "size"),
            quantidade_perfis_distintos=("ID", "nunique"),
        )
        .reset_index()
        .rename(columns={
            "Rede": "rede_social",
            "Casa de Aposta": "plataforma",
        })
        .sort_values(["rede_social", "quantidade_registros"], ascending=[True, False])
    )
    resultado.to_csv(
        SAIDA / "base2_frequencia_plataformas_por_rede.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    preparar_base1()
    preparar_base2()
    print("Arquivos agregados preparados em outputs/zenodo/:")
    print("- base1_frequencia_canais.csv")
    print("- base2_frequencia_plataformas_por_rede.csv")


if __name__ == "__main__":
    main()
