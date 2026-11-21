# Makefile — execução completa do projeto

# Prioriza o ambiente virtual do projeto, caso exista.
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
PIP := $(PYTHON) -m pip

.PHONY: all install clean run run-grafos run-lenad benchmark

# Comando padrão: instala as dependências.
all: install

install:
	$(PIP) install -r requirements.txt

# Remove somente resultados gerados e caches.
# Preserva os dados de entrada e outputs/grafo_base2.pdf (Gephi).
clean:
	rm -rf outputs/questionario
	rm -rf outputs/divulgacao_youtube_instagram
	rm -rf outputs/lenad
	rm -rf outputs/desempenho
	rm -rf __pycache__ src/__pycache__ .pytest_cache

# Executa todas as análises do projeto.
run: run-grafos run-lenad benchmark

# Bases 1 e 2: questionário e divulgação no YouTube/Instagram.
run-grafos:
	$(PYTHON) main.py --base todas

# Base 3: análise estatística do LENAD III.
run-lenad:
	$(PYTHON) src/lenad_visualization.py

# Avaliação de desempenho de BFS e DFS.
benchmark:
	$(PYTHON) benchmark_bfs_dfs.py
