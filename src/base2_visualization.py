"""Gráficos da análise da Base 2."""

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def gerar_visualizacoes(grafo: nx.DiGraph, dados: pd.DataFrame, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)

    # Grafo em três camadas. O PDF final organizado no Gephi é preservado.
    posicoes = nx.multipartite_layout(grafo, subset_key="camada", align="vertical")
    plt.figure(figsize=(19, 13))
    nos_rede = [n for n, a in grafo.nodes(data=True) if a["tipo"] == "rede_social"]
    nos_perfil = [n for n, a in grafo.nodes(data=True) if a["tipo"] == "perfil"]
    nos_casa = [n for n, a in grafo.nodes(data=True) if a["tipo"] == "plataforma"]

    larguras = [
        0.7 + 0.45 * (grafo[u][v].get("peso", 1) ** 0.5)
        for u, v in grafo.edges()
    ]
    nx.draw_networkx_edges(
        grafo, posicoes, alpha=0.35, arrows=True, arrowsize=10,
        width=larguras, connectionstyle="arc3,rad=0.04"
    )
    nx.draw_networkx_nodes(grafo, posicoes, nodelist=nos_rede, node_size=1700)
    nx.draw_networkx_nodes(grafo, posicoes, nodelist=nos_perfil, node_size=700)
    nx.draw_networkx_nodes(grafo, posicoes, nodelist=nos_casa, node_size=1100)
    rotulos = {n: a["label"] for n, a in grafo.nodes(data=True)}
    nx.draw_networkx_labels(grafo, posicoes, labels=rotulos, font_size=7)
    plt.title("Rede dirigida de divulgação: redes sociais, perfis e plataformas")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(saida / "grafo_base2_python.png", dpi=300, bbox_inches="tight")
    plt.close()

    identificados = dados[
        ~dados["Casa de Aposta"].str.casefold().isin(
            ["", "não identificada", "nao identificada",
             "não identificado", "nao identificado"]
        )
    ].copy()

    ranking_perfis = (
        identificados.groupby("Canal").size()
        .sort_values(ascending=True)
    )
    plt.figure(figsize=(10, max(5, len(ranking_perfis) * 0.32)))
    barras = plt.barh(ranking_perfis.index, ranking_perfis.values)
    plt.bar_label(barras, padding=3)
    plt.title("Publicações identificadas por perfil")
    plt.xlabel("Número de publicações")
    plt.tight_layout()
    plt.savefig(saida / "publicacoes_por_perfil.png", dpi=300, bbox_inches="tight")
    plt.close()

    ranking_casas = (
        identificados.groupby("Casa de Aposta").size()
        .sort_values(ascending=True)
    )
    plt.figure(figsize=(10, max(5, len(ranking_casas) * 0.32)))
    barras = plt.barh(ranking_casas.index, ranking_casas.values)
    plt.bar_label(barras, padding=3)
    plt.title("Publicações identificadas por plataforma")
    plt.xlabel("Número de publicações")
    plt.tight_layout()
    plt.savefig(saida / "publicacoes_por_plataforma.png", dpi=300, bbox_inches="tight")
    plt.close()

    resumo = dados.groupby("Rede").agg(
        registros=("ID", "size"),
        perfis=("ID", "nunique"),
    )
    plt.figure(figsize=(8, 5))
    barras = plt.bar(resumo.index, resumo["registros"])
    plt.bar_label(barras, padding=3)
    plt.title("Registros coletados por rede social")
    plt.xlabel("Rede social")
    plt.ylabel("Número de registros")
    plt.tight_layout()
    plt.savefig(saida / "registros_por_rede.png", dpi=300, bbox_inches="tight")
    plt.close()
