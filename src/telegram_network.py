#!/usr/bin/env python3
"""Analisa a rede direcionada de recomendações documentadas no Telegram.

Uso, na raiz do repositório:
    python src/telegram_network.py

O script preserva a exportação GEXF e gera tabelas reproduzíveis de métricas
em outputs/telegram/. As relações representam somente recomendações
documentadas nas páginas 26 e 28 do relatório utilizado.
"""
from pathlib import Path
import csv
import math
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
ENTRADA = ROOT / "data" / "relacoes_telegram_ibict.csv"
PASTA_SAIDA = ROOT / "outputs" / "telegram"
SAIDA_GEXF = PASTA_SAIDA / "rede_recomendacoes_telegram.gexf"
SAIDA_NOS = PASTA_SAIDA / "metricas_comunidades_telegram.csv"
SAIDA_COMPONENTES = PASTA_SAIDA / "componentes_telegram.csv"
SAIDA_RELATORIO = PASTA_SAIDA / "relatorio_metricas_telegram.txt"
CAMPOS = {
    "canal_origem", "canal_recomendado", "membros_origem",
    "membros_destino", "pagina_relatorio", "fonte"
}


def carregar_relacoes():
    if not ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {ENTRADA}")
    with ENTRADA.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltantes = CAMPOS - set(leitor.fieldnames or [])
        if faltantes:
            raise ValueError(f"Colunas ausentes no CSV: {sorted(faltantes)}")
        dados = list(leitor)
    if not dados:
        raise ValueError("O CSV não contém relações.")
    return dados


def construir_grafo(relacoes):
    grafo = nx.DiGraph()
    for numero, relacao in enumerate(relacoes, start=1):
        origem = relacao["canal_origem"].strip()
        destino = relacao["canal_recomendado"].strip()
        if not origem or not destino:
            raise ValueError(f"Relação {numero}: canal de origem/destino vazio.")
        try:
            membros_origem = int(relacao["membros_origem"])
            membros_destino = int(relacao["membros_destino"])
        except (TypeError, ValueError) as erro:
            raise ValueError(f"Relação {numero}: quantidade de membros inválida.") from erro
        for canal, membros in ((origem, membros_origem), (destino, membros_destino)):
            if canal in grafo and grafo.nodes[canal]["membros"] != membros:
                raise ValueError(
                    f"Quantidade de membros inconsistente para o canal: {canal}"
                )
            grafo.add_node(canal, tipo="canal", membros=membros)
        grafo.add_edge(
            origem, destino,
            tipo_relacao="recomendacao_documentada",
            pagina_relatorio=str(relacao["pagina_relatorio"]),
            fonte=relacao["fonte"],
        )
    return grafo


def calcular_metricas(grafo):
    total_nos = grafo.number_of_nodes()
    denominador = total_nos - 1
    intermediacao = nx.betweenness_centrality(
        grafo, normalized=True, endpoints=False
    ) if total_nos > 2 else {no: 0.0 for no in grafo}

    componentes = sorted(
        (set(c) for c in nx.weakly_connected_components(grafo)),
        key=lambda c: (-len(c), sorted(c)[0].casefold()),
    )
    componente_por_no = {}
    for indice, componente in enumerate(componentes, start=1):
        for no in componente:
            componente_por_no[no] = indice

    linhas_nos = []
    for no, atributos in sorted(grafo.nodes(data=True), key=lambda item: item[0].casefold()):
        grau_entrada = grafo.in_degree(no)
        grau_saida = grafo.out_degree(no)
        alcancaveis = len(nx.descendants(grafo, no))
        linhas_nos.append({
            "comunidade": no,
            "membros_informados_no_relatorio": atributos["membros"],
            "grau_entrada": grau_entrada,
            "grau_saida": grau_saida,
            "centralidade_entrada_normalizada": (
                grau_entrada / denominador if denominador else 0.0
            ),
            "centralidade_saida_normalizada": (
                grau_saida / denominador if denominador else 0.0
            ),
            "centralidade_intermediacao": intermediacao[no],
            "alcance_direcionado": alcancaveis,
            "componente_fraco": componente_por_no[no],
        })

    linhas_componentes = []
    for indice, componente in enumerate(componentes, start=1):
        subgrafo = grafo.subgraph(componente)
        linhas_componentes.append({
            "componente": indice,
            "quantidade_comunidades": len(componente),
            "quantidade_recomendacoes": subgrafo.number_of_edges(),
            "comunidades": " ; ".join(sorted(componente, key=str.casefold)),
        })

    n = total_nos
    m = grafo.number_of_edges()
    densidade = nx.density(grafo)
    resumo = {
        "vertices": n,
        "arestas": m,
        "componentes_fracamente_conexos": len(componentes),
        "tamanho_maior_componente": max(map(len, componentes), default=0),
        "tamanho_menor_componente": min(map(len, componentes), default=0),
        "densidade_direcionada": densidade,
        "grau_medio_entrada": sum(dict(grafo.in_degree()).values()) / n if n else 0,
        "grau_medio_saida": sum(dict(grafo.out_degree()).values()) / n if n else 0,
        "origens_com_recomendacoes": sum(1 for _, grau in grafo.out_degree() if grau > 0),
        "destinos_recomendados": sum(1 for _, grau in grafo.in_degree() if grau > 0),
    }
    return resumo, linhas_nos, linhas_componentes


def salvar_csv(caminho, linhas):
    if not linhas:
        return
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)


def salvar_relatorio(resumo, nos, componentes):
    linhas = [
        "RELATÓRIO DE MÉTRICAS — REDE DE RECOMENDAÇÕES DOCUMENTADAS NO TELEGRAM",
        "",
        "MÉTRICAS GERAIS",
        f"Vértices (comunidades): {resumo['vertices']}",
        f"Arestas (recomendações documentadas): {resumo['arestas']}",
        f"Componentes fracamente conexos: {resumo['componentes_fracamente_conexos']}",
        f"Maior componente (vértices): {resumo['tamanho_maior_componente']}",
        f"Menor componente (vértices): {resumo['tamanho_menor_componente']}",
        f"Densidade direcionada: {resumo['densidade_direcionada']:.6f} ({resumo['densidade_direcionada'] * 100:.2f}%)",
        f"Grau médio de entrada: {resumo['grau_medio_entrada']:.6f}",
        f"Grau médio de saída: {resumo['grau_medio_saida']:.6f}",
        f"Comunidades com pelo menos uma recomendação de saída: {resumo['origens_com_recomendacoes']}",
        f"Comunidades que recebem pelo menos uma recomendação: {resumo['destinos_recomendados']}",
        "",
        "COMPONENTES",
    ]
    for componente in componentes:
        linhas.append(
            f"Componente {componente['componente']}: "
            f"{componente['quantidade_comunidades']} comunidades e "
            f"{componente['quantidade_recomendacoes']} recomendações"
        )
        linhas.append(f"  {componente['comunidades']}")
    linhas.extend([
        "",
        "INTERPRETAÇÃO E LIMITAÇÕES",
        "O grau de saída conta recomendações registradas a partir de uma comunidade.",
        "O grau de entrada conta recomendações recebidas dentro deste conjunto de dados.",
        "O alcance direcionado conta outros vértices alcançáveis seguindo as setas.",
        "As centralidades são calculadas somente sobre os vértices e arestas deste arquivo.",
        "A amostra contém exemplos documentados nas páginas 26 e 28 do relatório.",
        "As relações não comprovam migração de usuários, influência efetiva ou causalidade.",
        "A ausência de uma aresta nesta amostra não prova que a relação não exista.",
        "Os números de membros são os valores registrados na fonte e não são pesos das arestas.",
        "",
        "ARQUIVOS GERADOS",
        SAIDA_GEXF.name,
        SAIDA_NOS.name,
        SAIDA_COMPONENTES.name,
        SAIDA_RELATORIO.name,
    ])
    SAIDA_RELATORIO.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main():
    relacoes = carregar_relacoes()
    grafo = construir_grafo(relacoes)
    resumo, metricas_nos, componentes = calcular_metricas(grafo)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(grafo, SAIDA_GEXF)
    salvar_csv(SAIDA_NOS, metricas_nos)
    salvar_csv(SAIDA_COMPONENTES, componentes)
    salvar_relatorio(resumo, metricas_nos, componentes)

    print("===== ANÁLISE DA REDE DE RECOMENDAÇÕES DOCUMENTADAS NO TELEGRAM =====")
    print(f"Vértices: {resumo['vertices']}")
    print(f"Arestas: {resumo['arestas']}")
    print(f"Componentes fracamente conexos: {resumo['componentes_fracamente_conexos']}")
    print(f"Densidade direcionada: {resumo['densidade_direcionada']:.4f} "
          f"({resumo['densidade_direcionada'] * 100:.2f}%)")
    print(f"Grau médio de entrada: {resumo['grau_medio_entrada']:.4f}")
    print(f"Grau médio de saída: {resumo['grau_medio_saida']:.4f}")
    print("\nArquivos gerados:")
    print(f"- Grafo GEXF: {SAIDA_GEXF}")
    print(f"- Métricas por comunidade: {SAIDA_NOS}")
    print(f"- Componentes: {SAIDA_COMPONENTES}")
    print(f"- Relatório textual: {SAIDA_RELATORIO}")
    print("\nLimitação: somente exemplos documentados nas páginas 26 e 28.")
    print("As arestas não comprovam migração, influência efetiva ou causalidade.")


if __name__ == "__main__":
    main()
