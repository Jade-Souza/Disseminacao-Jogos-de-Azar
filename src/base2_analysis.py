"""Análise da Base 2: rede social -> perfil -> plataforma de apostas.

O grafo é dirigido e possui três camadas. As arestas indicam a relação
registrada na coleta; elas não comprovam, por si só, influência causal.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

from src.bfs import busca_em_largura

ROOT = Path(__file__).resolve().parents[1]
ARQUIVO_ENTRADA = ROOT / "data" / "Pasta(base_youtube_instagram).csv"
PASTA_SAIDA = ROOT / "outputs" / "base2"

COLUNAS = [
    "ID", "Rede", "Canal", "Link do canal", "Video/Live",
    "Link do Video", "Data de Publicação", "Casa de Aposta",
    "Evidência de divulgação",
]

# Cada rede social será usada como vértice inicial de uma busca independente.
VERTICES_INICIAIS_BFS = {
    "YouTube": "rede::YouTube",
    "Instagram": "rede::Instagram",
}


def carregar_dados(caminho: Path = ARQUIVO_ENTRADA) -> pd.DataFrame:
    """Carrega e valida o CSV, preservando os registros da coleta."""
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo da Base 2 não encontrado: {caminho}")

    # CSVs exportados pelo Excel podem usar codificações diferentes.
    erro_codificacao = None
    for codificacao in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            dados = pd.read_csv(
                caminho, sep=";", encoding=codificacao, dtype=str
            )
            break
        except UnicodeDecodeError as erro:
            erro_codificacao = erro
    else:
        raise UnicodeError(
            f"Não foi possível decodificar o CSV {caminho}. "
            "Salve-o como CSV UTF-8 ou verifique sua codificação."
        ) from erro_codificacao

    # Remove espaços dos nomes das colunas e confere se o arquivo tem
    # todos os campos necessários para construir o grafo.
    dados.columns = dados.columns.str.strip()
    faltantes = [coluna for coluna in COLUNAS if coluna not in dados.columns]
    if faltantes:
        raise ValueError(f"Colunas ausentes no CSV: {', '.join(faltantes)}")

    # Padroniza valores vazios e espaços, sem excluir linhas da planilha.
    for coluna in COLUNAS:
        dados[coluna] = dados[coluna].fillna("").astype(str).str.strip()

    # Corrige variações de escrita para que a mesma rede não vire
    # vértices diferentes no grafo.
    dados["Rede"] = dados["Rede"].replace(
        {"Youtube": "YouTube", "youtube": "YouTube", "instagram": "Instagram"}
    )
    return dados


def casa_identificada(valor: str) -> bool:
    """Indica se o registro contém o nome de uma plataforma identificada."""
    texto = str(valor).strip().casefold()
    return texto not in {
        "", "não identificada", "nao identificada",
        "não identificado", "nao identificado"
    }


def construir_grafo(dados: pd.DataFrame) -> nx.DiGraph:
    """Constrói a rede dirigida com camadas de rede, perfil e plataforma."""
    grafo = nx.DiGraph()

    # Um vértice de perfil representa cada ID único da coleta. A remoção
    # de duplicatas aqui evita criar o mesmo perfil mais de uma vez.
    perfis = (
        dados[["ID", "Rede", "Canal", "Link do canal"]]
        .drop_duplicates(subset=["ID"])
    )

    # CAMADA 1: redes sociais (YouTube e Instagram).
    for rede in sorted(dados["Rede"].unique()):
        grafo.add_node(
            f"rede::{rede}", label=rede, tipo="rede_social",
            camada=0, rede=rede
        )

    # CAMADA 2: perfis/canais. A direção rede -> perfil representa
    # em qual rede social aquele perfil foi observado.
    for perfil in perfis.itertuples(index=False):
        identificador, rede, canal, link = perfil
        no_perfil = f"perfil::{identificador}"
        grafo.add_node(
            no_perfil, label=canal, tipo="perfil",
            camada=1, rede=rede, id_registro=identificador,
            link=link
        )
        grafo.add_edge(
            f"rede::{rede}", no_perfil,
            weight=1, peso=1, tipo_relacao="rede_perfil"
        )

    # Registros sem casa identificada continuam nas contagens descritivas,
    # mas não geram uma plataforma fictícia/genérica no grafo.
    identificados = dados[dados["Casa de Aposta"].map(casa_identificada)].copy()
    identificados["Casa de Aposta"] = identificados["Casa de Aposta"].str.strip()

    # CAMADA 3: um vértice para cada plataforma distinta identificada.
    for casa in sorted(identificados["Casa de Aposta"].unique()):
        grafo.add_node(
            f"casa::{casa}", label=casa, tipo="plataforma",
            camada=2, plataforma=casa
        )

    # Agrupa publicações do mesmo perfil para a mesma plataforma.
    # A quantidade de registros agrupados será o peso da aresta.
    contagens = (
        identificados.groupby(["ID", "Casa de Aposta"], dropna=False)
        .size()
        .reset_index(name="peso")
    )
    rede_por_id = perfis.set_index("ID")["Rede"].to_dict()

    # A direção perfil -> plataforma representa a plataforma identificada
    # nas publicações daquele perfil. O peso corresponde ao número de
    # publicações coletadas para aquela relação.
    for relacao in contagens.itertuples(index=False):
        identificador, casa, peso = relacao
        grafo.add_edge(
            f"perfil::{identificador}", f"casa::{casa}",
            weight=int(peso), peso=int(peso),
            tipo_relacao="perfil_plataforma",
            rede=rede_por_id.get(identificador, "")
        )

    return grafo


def executar_buscas_bfs(grafo: nx.DiGraph) -> dict[str, list[str]]:
    """Executa BFS a partir de cada rede social e registra a ordem de visita.

    Em um DiGraph, grafo.neighbors(vértice) retorna os sucessores:
    portanto, a busca respeita o sentido rede -> perfil -> plataforma.
    """
    resultados = {}

    for rede, vertice_inicial in VERTICES_INICIAIS_BFS.items():
        # A função de BFS compartilhada também é usada na Base 1.
        resultados[rede] = busca_em_largura(grafo, vertice_inicial)

    return resultados


def registrar_resultados_bfs(
    grafo: nx.DiGraph, resultados: dict[str, list[str]]
) -> None:
    """Adiciona a ordem de visita da BFS aos atributos dos vértices.

    O valor zero significa que o vértice não foi alcançado naquela busca.
    Esses atributos são exportados no GEXF e podem ser usados no Gephi.
    """
    for no in grafo.nodes:
        grafo.nodes[no]["ordem_bfs_youtube"] = 0
        grafo.nodes[no]["ordem_bfs_instagram"] = 0

    for rede, ordem in resultados.items():
        atributo = f"ordem_bfs_{rede.casefold()}"
        for posicao, no in enumerate(ordem, start=1):
            grafo.nodes[no][atributo] = posicao


def gerar_tabelas(
    grafo: nx.DiGraph,
    dados: pd.DataFrame,
    resultados_bfs: dict[str, list[str]]
) -> None:
    """Gera CSVs de vértices, arestas, rankings e percurso das buscas."""
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    # Grau conta arestas. Força ponderada soma os pesos dessas arestas.
    # Para arestas rede-perfil, o peso é 1; para perfil-plataforma,
    # o peso é o número de publicações identificadas na relação.
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

    # Exporta cada aresta com seu sentido, tipo de relação e peso.
    arestas = []
    for origem, destino, atributos in grafo.edges(data=True):
        arestas.append({"origem": origem, "destino": destino, **atributos})
    pd.DataFrame(arestas).to_csv(
        PASTA_SAIDA / "arestas.csv", index=False, encoding="utf-8-sig"
    )

    # Rankings usam os registros com plataforma identificada.
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

    # Salva uma linha por vértice visitado, identificando a rede de origem
    # e a posição em que o vértice foi alcançado pela BFS.
    linhas_bfs = []
    for rede, ordem in resultados_bfs.items():
        for posicao, no in enumerate(ordem, start=1):
            atributos = grafo.nodes[no]
            linhas_bfs.append({
                "rede_origem": rede,
                "ordem_visita": posicao,
                "id_vertice": no,
                "rotulo": atributos.get("label", no),
                "tipo": atributos.get("tipo", ""),
            })
    pd.DataFrame(linhas_bfs).to_csv(
        PASTA_SAIDA / "busca_largura.csv",
        index=False,
        encoding="utf-8-sig"
    )


def calcular_metricas(grafo: nx.DiGraph, dados: pd.DataFrame) -> dict:
    """Calcula métricas estruturais e descritivas da rede dirigida."""
    identificados = dados[dados["Casa de Aposta"].map(casa_identificada)].copy()
    nao_identificados = dados[~dados["Casa de Aposta"].map(casa_identificada)]
    perfis = dados[["ID", "Rede", "Canal"]].drop_duplicates("ID")
    plataformas = sorted(identificados["Casa de Aposta"].unique())

    # Cada par perfil-plataforma é uma relação distinta; seu peso é
    # a quantidade de publicações coletadas para esse par.
    relacoes = (
        identificados.groupby(["ID", "Casa de Aposta"])
        .size().reset_index(name="peso")
    )

    # Componentes fracamente conexas ignoram a direção das arestas.
    # Isso identifica agrupamentos conectados, mas não significa que
    # todos os vértices sejam alcançáveis uns a partir dos outros.
    componentes = list(nx.weakly_connected_components(grafo))
    maior_componente = max((len(componente) for componente in componentes), default=0)

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
            "plataformas_distintas": int(
                identificados_rede["Casa de Aposta"].nunique()
            ),
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
        # Densidade bipartida possível entre perfis e plataformas:
        # número de relações observadas dividido por perfis x plataformas.
        "densidade_perfil_plataforma": (
            round(len(relacoes) / (len(perfis) * len(plataformas)), 4)
            if perfis.shape[0] and plataformas else 0
        ),
        "peso_total_das_relacoes_perfil_plataforma": int(relacoes["peso"].sum()),
        "peso_minimo_relacao_perfil_plataforma": (
            int(relacoes["peso"].min()) if len(relacoes) else 0
        ),
        "peso_maximo_relacao_perfil_plataforma": (
            int(relacoes["peso"].max()) if len(relacoes) else 0
        ),
        "peso_medio_relacao_perfil_plataforma": (
            round(float(relacoes["peso"].mean()), 2) if len(relacoes) else 0
        ),
        "peso_mediano_relacao_perfil_plataforma": (
            float(relacoes["peso"].median()) if len(relacoes) else 0
        ),
        # Um DAG é um grafo dirigido sem ciclos; a estrutura em camadas
        # deve manter o sentido rede -> perfil -> plataforma.
        "grafo_dag": bool(nx.is_directed_acyclic_graph(grafo)),
        "distribuicao_por_rede": distribuicao_redes,
    }
    return metricas


def resumir_buscas_bfs(
    grafo: nx.DiGraph, resultados_bfs: dict[str, list[str]]
) -> None:
    """Mostra no terminal o total e a composição dos vértices visitados."""
    print("\n===== BUSCA EM LARGURA (BFS) — BASE 2 =====")

    for rede, ordem in resultados_bfs.items():
        tipos = Counter(grafo.nodes[no].get("tipo", "não classificado") for no in ordem)
        print(f"\nOrigem: {rede}")
        print(f"Total de vértices visitados: {len(ordem)}")
        print(f"Redes sociais: {tipos.get('rede_social', 0)}")
        print(f"Perfis: {tipos.get('perfil', 0)}")
        print(f"Plataformas: {tipos.get('plataforma', 0)}")
        print("Ordem de visita:")
        for posicao, no in enumerate(ordem, start=1):
            rotulo = grafo.nodes[no].get("label", no)
            tipo = grafo.nodes[no].get("tipo", "")
            print(f"  {posicao}. {rotulo} ({tipo})")


def executar_analise(caminho: Path = ARQUIVO_ENTRADA) -> nx.DiGraph:
    """Executa o fluxo completo: dados, grafo, BFS, métricas e arquivos."""
    dados = carregar_dados(caminho)
    grafo = construir_grafo(dados)
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    # Executa a BFS separadamente para comparar o que é alcançável
    # a partir de cada rede social, seguindo apenas arestas de saída.
    resultados_bfs = executar_buscas_bfs(grafo)
    registrar_resultados_bfs(grafo, resultados_bfs)
    resumir_buscas_bfs(grafo, resultados_bfs)

    # Gera tabelas com graus, forças ponderadas, relações e percurso BFS.
    gerar_tabelas(grafo, dados, resultados_bfs)

    # Calcula métricas gerais e mantém o arquivo JSON de resultados.
    metricas = calcular_metricas(grafo, dados)
    with (PASTA_SAIDA / "metricas.json").open("w", encoding="utf-8") as arquivo:
        json.dump(metricas, arquivo, ensure_ascii=False, indent=2)

    # O GEXF contém a estrutura do grafo e também a ordem de visita da BFS.
    nx.write_gexf(grafo, PASTA_SAIDA / "grafo_base2.gexf")

    print("\n===== MÉTRICAS ESTRUTURAIS — BASE 2 =====")
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
