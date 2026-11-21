from collections import deque


def busca_em_largura(grafo, inicio):
    """Executa BFS e retorna os vértices na ordem em que são visitados.

    Em grafos não dirigidos, percorre os vizinhos normalmente. Em um
    NetworkX DiGraph, grafo.neighbors(vértice) retorna apenas os sucessores,
    respeitando a direção das arestas.
    """
    if inicio not in grafo:
        raise ValueError(f"Vértice inicial não encontrado: {inicio}")

    # A fila FIFO garante que os vértices mais próximos da origem
    # sejam visitados antes dos vértices em níveis mais distantes.
    visitados = {inicio}
    fila = deque([inicio])
    ordem_visita = []

    while fila:
        vertice = fila.popleft()
        ordem_visita.append(vertice)

        # A ordenação torna a ordem de visita reproduzível entre execuções.
        for vizinho in sorted(grafo.neighbors(vertice)):
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

    return ordem_visita
