"""Análise reprodutível da Base 2: rede social -> perfil -> plataforma."""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARQUIVO_ENTRADA = ROOT / "data" / "Pasta(base_youtube_instagram).csv"
PASTA_SAIDA = ROOT / "outputs" / "base2"

COLUNAS = [
    "ID", "Rede", "Canal", "Link do canal", "Video/Live",
    "Link do Video", "Data de Publicação", "Casa de Aposta",
    "Evidência de divulgação",
]


def carregar_dados(caminho: Path = ARQUIVO_ENTRADA) -> pd.DataFrame:
    """Carrega o CSV original sem alterar seus registros."""
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo da Base 2 não encontrado: {caminho}")

    # A planilha exportada pode estar em UTF-8 ou Windows-1252
    # (comum em CSVs salvos pelo Excel em português).
    erro_utf8 = None
    for codificacao in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            dados = pd.read_csv(
                caminho, sep=";", encoding=codificacao, dtype=str
            )
            break
        except UnicodeDecodeError as erro:
            erro_utf8 = erro
    else:
        raise UnicodeError(
            f"Não foi possível decodificar o CSV {caminho}. "
            "Salve-o como CSV UTF-8 ou verifique sua codificação."
        ) from erro_utf8

    dados.columns = dados.columns.str.strip()
    faltantes = [coluna for coluna in COLUNAS if coluna not in dados.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(faltantes)}")

    for coluna in COLUNAS:
        dados[coluna] = dados[coluna].fillna("").astype(str).str.strip()

    dados["Rede"] = dados["Rede"].replace(
        {"Youtube": "YouTube", "youtube": "YouTube", "instagram": "Instagram"}
    )
    return dados


def casa_identificada(valor: str) -> bool:
    """Não cria vértice genérico para registros sem casa identificada."""
    texto = str(valor).strip().casefold()
    return texto not in {"", "não identificada", "nao identificada", "não identificado", "nao identificado"}


def construir_grafo(dados: pd.DataFrame) -> nx.DiGraph:
    """Cria grafo dirigido de três camadas: rede, perfil e plataforma."""
    grafo = nx.DiGraph()

    perfis = (
        dados[["ID", "Rede", "Canal", "Link do canal"]]
        .drop_duplicates(subset=["ID"])
    )

    for rede in sorted(dados["Rede"].unique()):
        grafo.add_node(
            f"rede::{rede}", label=rede, tipo="rede_social",
            camada=0, rede=rede
        )

    for perfil in perfis.itertuples(index=False):
        identificador, rede, canal, link = perfil
        no_perfil = f"perfil::{identificador}"
        grafo.add_node(
            no_perfil, label=canal, tipo="perfil",
            camada=1, rede=rede, id_registro=identificador,
            link=link
        )
        grafo.add_edge(
            f"rede::{rede}", no_perfil, weight=1, peso=1,
            tipo_relacao="rede_perfil"
        )

    identificados = dados[dados["Casa de Aposta"].map(casa_identificada)].copy()
    identificados["Casa de Aposta"] = identificados["Casa de Aposta"].str.strip()

    for casa in sorted(identificados["Casa de Aposta"].unique()):
        grafo.add_node(
            f"casa::{casa}", label=casa, tipo="plataforma",
            camada=2, plataforma=casa
        )

    contagens = (
        identificados.groupby(["ID", "Casa de Aposta"], dropna=False)
        .size()
        .reset_index(name="peso")
    )
    rede_por_id = perfis.set_index("ID")["Rede"].to_dict()

    for relacao in contagens.itertuples(index=False):
        identificador, casa, peso = relacao
        grafo.add_edge(
            f"perfil::{identificador}", f"casa::{casa}",
            weight=int(peso), peso=int(peso), tipo_relacao="perfil_plataforma",
            rede=rede_por_id.get(identificador, "")
        )

    return grafo


def gerar_tabelas(grafo: nx.DiGraph, dados: pd.DataFrame) -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    vertices = []
    for no, atributos in grafo.nodes(data=True):
        vertices.append({
            "id": no,
            **atributos,
            "grau_entrada": grafo.in_degree(no),
            "grau_saida": grafo.out_degree(no),
            "forca_entrada": grafo.in_degree(no, weight="weight"),
            "forca_saida": grafo.out_degree(no, weight="weight"),
        })
    pd.DataFrame(vertices).to_csv(
        PASTA_SAIDA / "vertices.csv", index=False, encoding="utf-8-sig"
    )

    arestas = []
    for origem, destino, atributos in grafo.edges(data=True):
        arestas.append({"origem": origem, "destino": destino, **atributos})
    pd.DataFrame(arestas).to_csv(
        PASTA_SAIDA / "arestas.csv", index=False, encoding="utf-8-sig"
    )

    identificados = dados[dados["Casa de Aposta"].map(casa_identificada)]
    ranking_perfis = (
        identificados.groupby(["ID", "Canal", "Rede"])
        .size().reset_index(name="publicacoes_identificadas")
        .sort_values("publicacoes_identificadas", ascending=False)
    )
    ranking_perfis.to_csv(
        PASTA_SAIDA / "ranking_perfis.csv", index=False, encoding="utf-8-sig"
    )

    ranking_casas = (
        identificados.groupby("Casa de Aposta").size()
        .reset_index(name="publicacoes_identificadas")
        .sort_values("publicacoes_identificadas", ascending=False)
    )
    ranking_casas.to_csv(
        PASTA_SAIDA / "ranking_plataformas.csv", index=False, encoding="utf-8-sig"
    )


def calcular_metricas(grafo: nx.DiGraph, dados: pd.DataFrame) -> dict:
    identificados = dados[dados["Casa de Aposta"].map(casa_identificada)].copy()
    nao_identificados = dados[~dados["Casa de Aposta"].map(casa_identificada)]
    perfis = dados[["ID", "Rede", "Canal"]].drop_duplicates("ID")
    plataformas = sorted(identificados["Casa de Aposta"].unique())

    relacoes = (
        identificados.groupby(["ID", "Casa de Aposta"])
        .size().reset_index(name="peso")
    )
    componentes = list(nx.weakly_connected_components(grafo))
    maior_componente = max((len(c) for c in componentes), default=0)
    distribuicao_redes = {}

    for rede, grupo in dados.groupby("Rede"):
        ids = grupo["ID"].unique()
        identificados_rede = identificados[identificados["ID"].isin(ids)]
        distribuicao_redes[rede] = {
            "registros_coletados": int(len(grupo)),
            "perfis": int(grupo["ID"].nunique()),
            "registros_com_plataforma_identificada": int(len(identificados_rede)),
            "registros_sem_plataforma_identificada": int(
                len(grupo) - len(identificados_rede)
            ),
            "plataformas_distintas": int(identificados_rede["Casa de Aposta"].nunique()),
        }

    metricas = {
        "registros_coletados": int(len(dados)),
        "redes_sociais": int(dados["Rede"].nunique()),
        "perfis": int(perfis["ID"].nunique()),
        "plataformas_identificadas": int(len(plataformas)),
        "vertices": int(grafo.number_of_nodes()),
        "arestas_dirigidas": int(grafo.number_of_edges()),
        "registros_com_plataforma_identificada": int(len(identificados)),
        "registros_sem_plataforma_identificada": int(len(nao_identificados)),
        "relacoes_distintas_perfil_plataforma": int(len(relacoes)),
        "componentes_fracamente_conexas": int(len(componentes)),
        "vertices_na_maior_componente_fraca": int(maior_componente),
        "densidade_perfil_plataforma": (
            round(len(relacoes) / (len(perfis) * len(plataformas)), 4)
            if perfis.shape[0] and plataformas else 0
        ),
        "peso_total_das_relacoes_perfil_plataforma": int(relacoes["peso"].sum()),
        "peso_minimo_relacao_perfil_plataforma": int(relacoes["peso"].min()) if len(relacoes) else 0,
        "peso_maximo_relacao_perfil_plataforma": int(relacoes["peso"].max()) if len(relacoes) else 0,
        "peso_medio_relacao_perfil_plataforma": round(float(relacoes["peso"].mean()), 2) if len(relacoes) else 0,
        "peso_mediano_relacao_perfil_plataforma": float(relacoes["peso"].median()) if len(relacoes) else 0,
        "grafo_dag": bool(nx.is_directed_acyclic_graph(grafo)),
        "distribuicao_por_rede": distribuicao_redes,
    }
    return metricas


def executar_analise(caminho: Path = ARQUIVO_ENTRADA) -> nx.DiGraph:
    dados = carregar_dados(caminho)
    grafo = construir_grafo(dados)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    gerar_tabelas(grafo, dados)
    metricas = calcular_metricas(grafo, dados)
    with (PASTA_SAIDA / "metricas.json").open("w", encoding="utf-8") as arquivo:
        json.dump(metricas, arquivo, ensure_ascii=False, indent=2)

    nx.write_gexf(grafo, PASTA_SAIDA / "grafo_base2.gexf")
    print("\n===== ANÁLISE DA BASE 2 =====")
    for chave, valor in metricas.items():
        if chave != "distribuicao_por_rede":
            print(f"{chave}: {valor}")
    print("\nDistribuição por rede:")
    for rede, valores in metricas["distribuicao_por_rede"].items():
        print(f"- {rede}: {valores}")

    print(f"\nResultados salvos em: {PASTA_SAIDA}")
    return grafo


if __name__ == "__main__":
    executar_analise()
