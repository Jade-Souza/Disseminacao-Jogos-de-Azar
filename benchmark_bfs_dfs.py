from pathlib import Path
from time import perf_counter_ns
from statistics import median, mean
import csv
import random

import networkx as nx
import matplotlib.pyplot as plt

from src.graph_builder import carregar_dados, construir_grafo
from src.bfs import busca_em_largura
from src.dfs import busca_em_profundidade


# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

INICIO = "Instagram"
REPETICOES_REAL = 1000
REPETICOES_SINTETICO = 200

# Quantidade de participantes nos grafos sintéticos.
TAMANHOS = [109, 250, 500, 1000, 2000, 4000]

PASTA_SAIDA = Path("outputs") / "desempenho"
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)


# ==========================================================
# MEDIÇÃO DO TEMPO
# ==========================================================

def medir_algoritmo(funcao, grafo, inicio, repeticoes):
    """Mede o tempo de execução e retorna estatísticas das repetições."""

    # Aquecimento: a execução não entra nas medições.
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


# ==========================================================
# BENCHMARK DO GRAFO REAL DO QUESTIONÁRIO
# ==========================================================

def benchmark_grafo_real():
    print("\n===== BENCHMARK DO GRAFO REAL =====")

    dados = carregar_dados()
    grafo = construir_grafo(dados)

    print(f"Vértices: {grafo.number_of_nodes()}")
    print(f"Arestas: {grafo.number_of_edges()}")

    if INICIO not in grafo:
        raise ValueError(f"O vértice inicial '{INICIO}' não existe no grafo.")

    algoritmos = {
        "BFS": busca_em_largura,
        "DFS": busca_em_profundidade,
    }

    resultados = []

    for nome, funcao in algoritmos.items():
        medicao = medir_algoritmo(
            funcao, grafo, INICIO, REPETICOES_REAL
        )

        registro = {
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

    caminho_csv = PASTA_SAIDA / "tempos_grafo_real.csv"
    with caminho_csv.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=resultados[0].keys())
        escritor.writeheader()
        escritor.writerows(resultados)

    plt.figure(figsize=(8, 5))
    nomes = [r["algoritmo"] for r in resultados]
    tempos = [r["tempo_mediano_ms"] for r in resultados]
    barras = plt.bar(nomes, tempos)

    plt.title("Tempo de execução de BFS e DFS no grafo real")
    plt.xlabel("Algoritmo")
    plt.ylabel("Tempo mediano (ms)")
    plt.bar_label(barras, labels=[f"{t:.6f} ms" for t in tempos], padding=4)
    plt.tight_layout()
    plt.savefig(PASTA_SAIDA / "tempo_bfs_dfs_grafo_real.png", dpi=300)
    plt.close()

    return grafo


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
            # Liga os canais em um ciclo, garantindo uma componente conectada.
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
# TESTE DE ESCALABILIDADE
# ==========================================================

def benchmark_escalabilidade():
    print("\n===== BENCHMARK DE ESCALABILIDADE =====")

    algoritmos = {
        "BFS": busca_em_largura,
        "DFS": busca_em_profundidade,
    }

    resultados = []

    for tamanho in TAMANHOS:
        grafo = gerar_grafo_sintetico(tamanho)

        print(
            f"\nGrafo: {grafo.number_of_nodes()} vértices; "
            f"{grafo.number_of_edges()} arestas"
        )

        for nome, funcao in algoritmos.items():
            medicao = medir_algoritmo(
                funcao, grafo, INICIO, REPETICOES_SINTETICO
            )

            registro = {
                "algoritmo": nome,
                "participantes": tamanho,
                "vertices_grafo": grafo.number_of_nodes(),
                "arestas_grafo": grafo.number_of_edges(),
                **medicao,
            }
            resultados.append(registro)

            print(
                f"{nome}: mediana = "
                f"{medicao['tempo_mediano_ms']:.6f} ms; "
                f"visitados = {medicao['vertices_visitados']}"
            )

    caminho_csv = PASTA_SAIDA / "escalabilidade_bfs_dfs.csv"
    with caminho_csv.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=resultados[0].keys())
        escritor.writeheader()
        escritor.writerows(resultados)

    plt.figure(figsize=(9, 5))

    for nome in ("BFS", "DFS"):
        dados_algoritmo = [r for r in resultados if r["algoritmo"] == nome]
        x = [r["vertices_grafo"] for r in dados_algoritmo]
        y = [r["tempo_mediano_ms"] for r in dados_algoritmo]
        plt.plot(x, y, marker="o", label=nome)

    plt.title("Escalabilidade de BFS e DFS em grafos bipartidos")
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
    benchmark_grafo_real()
    benchmark_escalabilidade()

    print("\n===== BENCHMARK CONCLUÍDO =====")
    print(f"Arquivos salvos em: {PASTA_SAIDA}")
