"""Benchmark de BFS e DFS nas Bases 1 e 2 e teste de escalabilidade.

Base 1: compara BFS e DFS no grafo real do questionário.
Base 2: mede BFS separadamente a partir de YouTube e Instagram.
Escalabilidade: compara BFS e DFS em grafos bipartidos sintéticos.
"""

from pathlib import Path
from time import perf_counter_ns
from statistics import median, mean
import csv
import random

import networkx as nx
import matplotlib.pyplot as plt

from src.graph_builder import carregar_dados as carregar_dados_base1
from src.graph_builder import construir_grafo as construir_grafo_base1
from src.divulgacao_youtube_instagram import (
    carregar_dados as carregar_dados_base2,
    construir_grafo as construir_grafo_base2,
    VERTICES_INICIAIS_BFS,
)
from src.bfs import busca_em_largura
from src.dfs import busca_em_profundidade


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INICIO_BASE1 = "Instagram"
REPETICOES_REAL = 1000
REPETICOES_SINTETICO = 200
TAMANHOS = [109, 250, 500, 1000, 2000, 4000]

ROOT = Path(__file__).resolve().parent
PASTA_SAIDA = ROOT / "outputs" / "desempenho"


# ==========================================================
# MEDIÇÃO DO TEMPO
# ==========================================================

def medir_algoritmo(funcao, grafo, inicio, repeticoes):
    """Mede o tempo de execução e retorna estatísticas das repetições."""
    # Aquecimento: esta execução não entra nas medições.
    funcao(grafo, inicio)

    tempos = []
    vertices_visitados = 0

    for _ in range(repeticoes):
        inicio_tempo = perf_counter_ns()
        resultado = funcao(grafo, inicio)
        fim_tempo = perf_counter_ns()

        tempos.append((fim_tempo - inicio_tempo) / 1_000_000)
        vertices_visitados = len(resultado)

    return {
        "tempo_mediano_ms": median(tempos),
        "tempo_medio_ms": mean(tempos),
        "vertices_visitados": vertices_visitados,
        "repeticoes": repeticoes,
    }


def salvar_csv(nome_arquivo, resultados):
    """Salva os resultados de uma medição em CSV."""
    if not resultados:
        return

    caminho = PASTA_SAIDA / nome_arquivo
    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=resultados[0].keys())
        escritor.writeheader()
        escritor.writerows(resultados)


def gerar_grafico_barras(titulo, eixo_x, eixo_y, nomes, tempos, caminho):
    """Gera gráfico de barras com os tempos medianos."""
    plt.figure(figsize=(8, 5))
    barras = plt.bar(nomes, tempos)
    plt.title(titulo)
    plt.xlabel(eixo_x)
    plt.ylabel(eixo_y)
    plt.bar_label(
        barras,
        labels=[f"{tempo:.6f} ms" for tempo in tempos],
        padding=4
    )
    plt.tight_layout()
    plt.savefig(PASTA_SAIDA / caminho, dpi=300)
    plt.close()


# ==========================================================
# BASE 1 — QUESTIONÁRIO: BFS E DFS NO GRAFO REAL
# ==========================================================

def benchmark_base1():
    print("\n===== DESEMPENHO — BASE 1 (QUESTIONÁRIO) =====")

    dados = carregar_dados_base1()
    grafo = construir_grafo_base1(dados)

    print(f"Vértices: {grafo.number_of_nodes()}")
    print(f"Arestas: {grafo.number_of_edges()}")
    print(f"Vértice inicial: {INICIO_BASE1}")

    if INICIO_BASE1 not in grafo:
        raise ValueError(
            f"O vértice inicial {INICIO_BASE1!r} não existe no grafo da Base 1."
        )

    algoritmos = {
        "BFS": busca_em_largura,
        "DFS": busca_em_profundidade,
    }
    resultados = []

    for nome, funcao in algoritmos.items():
        medicao = medir_algoritmo(
            funcao, grafo, INICIO_BASE1, REPETICOES_REAL
        )
        registro = {
            "base": "Base 1 - Questionário",
            "origem": INICIO_BASE1,
            "algoritmo": nome,
            "vertices_grafo": grafo.number_of_nodes(),
            "arestas_grafo": grafo.number_of_edges(),
            **medicao,
        }
        resultados.append(registro)

        print(f"\n{nome}")
        print(f"Vértices visitados: {medicao['vertices_visitados']}")
        print(f"Tempo mediano: {medicao['tempo_mediano_ms']:.6f} ms")
        print(f"Tempo médio: {medicao['tempo_medio_ms']:.6f} ms")

    salvar_csv("desempenho_base1.csv", resultados)
    gerar_grafico_barras(
        "Tempo de execução de BFS e DFS — Base 1",
        "Algoritmo",
        "Tempo mediano (ms)",
        [r["algoritmo"] for r in resultados],
        [r["tempo_mediano_ms"] for r in resultados],
        "tempo_base1_bfs_dfs.png",
    )
    return resultados


# ==========================================================
# BASE 2 — DIVULGAÇÃO: BFS A PARTIR DE CADA REDE SOCIAL
# ==========================================================

def benchmark_base2():
    print("\n===== DESEMPENHO — BASE 2 (DIVULGAÇÃO) =====")

    dados = carregar_dados_base2()
    grafo = construir_grafo_base2(dados)

    print(f"Vértices: {grafo.number_of_nodes()}")
    print(f"Arestas dirigidas: {grafo.number_of_edges()}")
    print("Algoritmo medido: BFS (respeitando a direção das arestas)")

    resultados = []

    for rede, vertice_inicial in VERTICES_INICIAIS_BFS.items():
        if vertice_inicial not in grafo:
            raise ValueError(
                f"O vértice inicial {vertice_inicial!r} não existe no grafo da Base 2."
            )

        medicao = medir_algoritmo(
            busca_em_largura, grafo, vertice_inicial, REPETICOES_REAL
        )
        registro = {
            "base": "Base 2 - Divulgação",
            "origem": rede,
            "algoritmo": "BFS",
            "vertices_grafo": grafo.number_of_nodes(),
            "arestas_grafo": grafo.number_of_edges(),
            **medicao,
        }
        resultados.append(registro)

        print(f"\nOrigem: {rede}")
        print(f"Vértices visitados: {medicao['vertices_visitados']}")
        print(f"Tempo mediano: {medicao['tempo_mediano_ms']:.6f} ms")
        print(f"Tempo médio: {medicao['tempo_medio_ms']:.6f} ms")

    salvar_csv("desempenho_base2.csv", resultados)
    gerar_grafico_barras(
        "Tempo de execução da BFS — Base 2",
        "Rede social de origem",
        "Tempo mediano (ms)",
        [r["origem"] for r in resultados],
        [r["tempo_mediano_ms"] for r in resultados],
        "tempo_base2_bfs.png",
    )
    return resultados


# ==========================================================
# GERAÇÃO DE GRAFOS BIPARTIDOS SINTÉTICOS
# ==========================================================

def gerar_grafo_sintetico(quantidade_participantes, semente=42):
    """Gera grafo bipartido com nove canais e n participantes."""
    gerador = random.Random(semente + quantidade_participantes)

    canais = [
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

    grafo = nx.Graph()
    grafo.add_nodes_from(canais, bipartite=1)

    for indice in range(quantidade_participantes):
        participante = f"Participante_{indice + 1}"
        grafo.add_node(participante, bipartite=0)

        if indice < len(canais):
            # Forma um ciclo entre os canais e garante uma componente conectada.
            canais_escolhidos = [
                canais[indice],
                canais[(indice + 1) % len(canais)],
            ]
        else:
            quantidade_canais = gerador.choice([2, 3])
            canais_escolhidos = gerador.sample(canais, quantidade_canais)

        for canal in canais_escolhidos:
            grafo.add_edge(participante, canal)

    return grafo


# ==========================================================
# TESTE DE ESCALABILIDADE — GRAFOS SINTÉTICOS DA BASE 1
# ==========================================================

def benchmark_escalabilidade():
    print("\n===== ESCALABILIDADE — GRAFOS SINTÉTICOS =====")

    algoritmos = {
        "BFS": busca_em_largura,
        "DFS": busca_em_profundidade,
    }
    resultados = []

    for tamanho in TAMANHOS:
        grafo = gerar_grafo_sintetico(tamanho)
        print(
            f"\nGrafo com {tamanho} participantes: "
            f"{grafo.number_of_nodes()} vértices e "
            f"{grafo.number_of_edges()} arestas"
        )

        for nome, funcao in algoritmos.items():
            medicao = medir_algoritmo(
                funcao, grafo, INICIO_BASE1, REPETICOES_SINTETICO
            )
            registro = {
                "base": "Grafos sintéticos - estrutura da Base 1",
                "algoritmo": nome,
                "participantes": tamanho,
                "vertices_grafo": grafo.number_of_nodes(),
                "arestas_grafo": grafo.number_of_edges(),
                **medicao,
            }
            resultados.append(registro)

            print(
                f"{nome}: mediana = {medicao['tempo_mediano_ms']:.6f} ms; "
                f"visitados = {medicao['vertices_visitados']}"
            )

    salvar_csv("escalabilidade_bfs_dfs.csv", resultados)

    plt.figure(figsize=(9, 5))
    for nome in ("BFS", "DFS"):
        dados_algoritmo = [r for r in resultados if r["algoritmo"] == nome]
        x = [r["vertices_grafo"] for r in dados_algoritmo]
        y = [r["tempo_mediano_ms"] for r in dados_algoritmo]
        plt.plot(x, y, marker="o", label=nome)

    plt.title("Escalabilidade de BFS e DFS em grafos bipartidos sintéticos")
    plt.xlabel("Quantidade de vértices")
    plt.ylabel("Tempo mediano de execução (ms)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PASTA_SAIDA / "escalabilidade_bfs_dfs.png", dpi=300)
    plt.close()


# ==========================================================
# EXECUÇÃO
# ==========================================================

if __name__ == "__main__":
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    resultados_base1 = benchmark_base1()
    resultados_base2 = benchmark_base2()
    benchmark_escalabilidade()

    todos_resultados = resultados_base1 + resultados_base2
    salvar_csv("desempenho_bases_reais.csv", todos_resultados)

    print("\n===== BENCHMARK CONCLUÍDO =====")
    print("As medições das Bases 1 e 2 foram salvas separadamente e em conjunto.")
    print(f"Arquivos salvos em: {PASTA_SAIDA}")
