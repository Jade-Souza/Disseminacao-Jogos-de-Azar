"""Prepara versões agregadas das Bases 1 e 2 para depósito público no Zenodo.

Não exporta respostas individuais, nomes de perfis, URLs, títulos ou links
de publicações. A Base 2 usa o campo ID como identificador interno de perfil;
esse identificador é contado apenas durante a agregação e não é exportado.
"""
from pathlib import Path
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
    "Instagram", "YouTube", "Influenciadores", "Amigos/conhecidos",
    "TikTok", "Sites esportivos", "Facebook", "Outro", "X/Twitter",
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

    total = int(len(dados))
    resultado = pd.DataFrame([
        {
            "canal": canal,
            "participantes_que_mencionaram": quantidade,
            "percentual_dos_participantes": (
                round(100 * quantidade / total, 2) if total else 0
            ),
            "total_participantes_questionario": total,
        }
        for canal, quantidade in frequencias.items()
    ])
    resultado.to_csv(
        SAIDA / "base1_frequencia_canais.csv",
        index=False, encoding="utf-8-sig",
    )
    print(f"Base 1: {total} participantes; {len(resultado)} canais agregados.")


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
    """Agrupa registros por rede/plataforma e conta perfis pelo ID interno."""
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

    obrigatorias = {"ID", "Rede", "Canal", "Casa de Aposta"}
    faltantes = obrigatorias.difference(dados.columns)
    if faltantes:
        raise ValueError(
            "Colunas ausentes na Base 2: " + ", ".join(sorted(faltantes))
        )

    dados["ID"] = dados["ID"].fillna("").str.strip()
    dados["Canal"] = dados["Canal"].fillna("").str.strip()
    if (dados["ID"] == "").any() or (dados["Canal"] == "").any():
        raise ValueError("Há registros sem ID ou sem nome de perfil/canal.")

    dados["Rede"] = dados["Rede"].fillna("").map(normalizar_rede)
    dados["Casa de Aposta"] = (
        dados["Casa de Aposta"].fillna("").map(normalizar_plataforma)
    )

    # Confirma que cada ID interno identifica um único perfil e uma única rede.
    validacao = dados.groupby("ID").agg(
        nomes=("Canal", "nunique"),
        redes=("Rede", "nunique"),
    )
    inconsistentes = validacao[
        (validacao["nomes"] != 1) | (validacao["redes"] != 1)
    ]
    if not inconsistentes.empty:
        raise ValueError(
            "Um ou mais IDs estão associados a nomes ou redes diferentes: "
            + ", ".join(inconsistentes.index.astype(str).tolist())
        )

    total_registros = len(dados)
    total_perfis = dados["ID"].nunique()

    # ID é a chave interna atribuída a cada perfil na planilha.
    # Contamos IDs distintos dentro de cada grupo, mas nunca os exportamos.
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
        .sort_values(
            ["rede_social", "quantidade_registros"],
            ascending=[True, False],
        )
    )

    if int(resultado["quantidade_registros"].sum()) != total_registros:
        raise RuntimeError("A soma dos registros agregados não confere.")
    if int(resultado["quantidade_perfis_distintos"].sum()) < total_perfis:
        raise RuntimeError("A contagem agregada de perfis não confere.")

    resultado.to_csv(
        SAIDA / "base2_frequencia_plataformas_por_rede.csv",
        index=False, encoding="utf-8-sig",
    )
    print(
        f"Base 2: {total_registros} registros; {total_perfis} perfis "
        f"distintos; {dados['Rede'].nunique()} redes."
    )
    print(
        "Validação: soma dos registros nas categorias = "
        f"{int(resultado['quantidade_registros'].sum())}."
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
