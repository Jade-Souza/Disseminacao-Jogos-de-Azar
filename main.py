"""Ponto de entrada das análises das Bases 1 e 2."""

import argparse
from pathlib import Path

import networkx as nx

from src.graph_builder import carregar_dados, construir_grafo
from src.bfs import busca_em_largura
from src.dfs import busca_em_profundidade
from src.metrics import analisar_metricas
from src.visualization import (
    gerar_ranking_canais,
    gerar_grafico_faixa_etaria,
    gerar_grafico_exposicao,
)

ROOT = Path(__file__).resolve().parent.parent


def executar_base1():
    """Executa a análise bipartida do questionário (Base 1)."""
    dados = carregar_dados()
    grafo = construir_grafo(dados)

    inicio = "Instagram"
    resultado_bfs = busca_em_largura(grafo, inicio)
    resultado_dfs = busca_em_profundidade(grafo, inicio)

    print("\n===== BUSCA EM LARGURA (BFS) — BASE 1 =====")
    print(f"Total visitado: {len(resultado_bfs)}")
    print("\n===== BUSCA EM PROFUNDIDADE (DFS) — BASE 1 =====")
    print(f"Total visitado: {len(resultado_dfs)}")

    analisar_metricas(grafo)

    pasta_outputs = ROOT / "outputs" / "questionario"
    pasta_outputs.mkdir(parents=True, exist_ok=True)
    caminho_gexf = pasta_outputs / "grafo_apostas.gexf"
    nx.write_gexf(grafo, caminho_gexf)

    gerar_ranking_canais(grafo)
    gerar_grafico_faixa_etaria(dados)
    gerar_grafico_exposicao(dados)

    print(f"\nArquivos da Base 1 salvos em {pasta_outputs}/.")


def executar_base2():
    """Executa a análise dirigida de três camadas (Base 2)."""
    from src.divulgacao_youtube_instagram import executar_analise
    executar_analise()


def main():
    parser = argparse.ArgumentParser(
        description="Análises das redes de influência dos jogos de azar online."
    )
    parser.add_argument(
        "--base", choices=["1", "2", "todas"], default="1",
        help="Base a analisar. O padrão 1 mantém o comportamento anterior."
    )
    args = parser.parse_args()

    if args.base in ("1", "todas"):
        executar_base1()
    if args.base in ("2", "todas"):
        executar_base2()


if __name__ == "__main__":
    main()