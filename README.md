# Disseminação dos Jogos de Azar Online no Brasil

Projeto acadêmico que investiga a disseminação de conteúdos relacionados a jogos de azar online no Brasil, utilizando a Teoria dos Grafos e análise estatística descritiva.

## Dados da pesquisa

As bases são analisadas separadamente, pois possuem unidades de análise e objetivos diferentes:

| Base | Conteúdo | Abordagem |
|---|---|---|
| **Base 1 — Questionário** | Respostas sobre canais de contato com conteúdos relacionados a jogos de azar online. | Grafo bipartido não dirigido e análise de métricas. |
| **Base 2 — YouTube e Instagram** | Registros de divulgação de plataformas de apostas em redes sociais. | Grafo dirigido em três camadas: rede social, perfil/canal e plataforma. |
| **Base 3 — LENAD III** | Indicadores estatísticos relacionados a apostas e suas consequências. | Análise estatística descritiva, sem construção de grafo. |

### Dados públicos

As versões agregadas das Bases 1 e 2 estão disponíveis no Zenodo:

- **DOI:** [10.5281/zenodo.24422317](https://doi.org/10.5281/zenodo.24422317)
- **Registro:** [Consultar e acessar os arquivos no Zenodo](https://zenodo.org/records/24422317)

O depósito disponibiliza tabelas agregadas. Não contém respostas individuais, identificadores de participantes, nomes de perfis ou links de publicações. A Base 3 (LENAD III) não faz parte desse depósito.

Os arquivos agregados permitem consultar frequências e distribuições, mas não permitem reconstruir integralmente os grafos originais nem reproduzir todas as operações realizadas com os dados de entrada.

## Estrutura do projeto

```text
Disseminacao-Jogos-de-Azar/
├── data/                              # Dados de entrada locais (não versionados)
├── docs/
│   ├── README_ZENODO.md               # Informações sobre o depósito dos dados
│   └── figuras_tabelas_overleaf.tex   # Figuras e tabelas para inclusão no Overleaf
├── outputs/
│   ├── questionario/                  # Resultados da Base 1
│   ├── divulgacao_youtube_instagram/  # Resultados da Base 2
│   ├── lenad/                         # Gráficos da Base 3
│   ├── desempenho/                    # Resultados dos benchmarks
│   ├── zenodo/                        # Arquivos relacionados ao depósito
│   ├── grafo_gephi.png                # Visualização da Base 1
│   └── grafo_apostas2.pdf             # Visualização da Base 2
├── src/
│   ├── bfs.py                         # Busca em largura
│   ├── dfs.py                         # Busca em profundidade
│   ├── graph_builder.py               # Construção do grafo da Base 1
│   ├── metrics.py                     # Métricas dos grafos
│   ├── visualization.py               # Visualizações da Base 1
│   ├── divulgacao_youtube_instagram.py # Análise da Base 2
│   ├── base2_visualization.py         # Visualizações da Base 2
│   └── lenad_visualization.py         # Gráficos estatísticos da Base 3
├── .gitignore                         # Arquivos e pastas ignorados pelo Git
├── benchmark_bfs_dfs.py               # Experimentos de desempenho BFS/DFS
├── main.py                            # Ponto de entrada das Bases 1 e 2
├── preparar_zenodo.py                 # Preparação dos arquivos para o Zenodo
├── Makefile                           # Instalação, limpeza e execução
└── requirements.txt                   # Dependências Python
```

> A pasta `data/` é necessária para executar as análises, mas não é publicada neste repositório. Os arquivos de entrada devem ser obtidos e colocados localmente nessa pasta, respeitando os nomes e formatos esperados pelos scripts. O conteúdo agregado do Zenodo não substitui todos os dados de entrada necessários para reproduzir os grafos completos.

## Requisitos

- Python 3.10 ou superior;
- GNU Make;
- Dados de entrada disponibilizados localmente na pasta `data/`.

## Instalação e execução

Na raiz do projeto, execute os comandos abaixo, nesta ordem:

```bash
make
make clean
make run
```

### O que cada comando faz

| Comando | Função |
|---|---|
| `make` | Instala as dependências listadas em `requirements.txt`. Prioriza o Python do ambiente virtual `.venv`, caso exista. |
| `make clean` | Remove os resultados gerados das análises e os caches, preservando os dados de entrada e os arquivos `outputs/grafo_gephi.png` e `outputs/grafo_apostas2.pdf`. |
| `make run` | Executa as análises das Bases 1 e 2, os gráficos da Base 3 e os benchmarks de BFS e DFS. |

### Execuções individuais

Também é possível executar partes do projeto separadamente:

```bash
make run-grafos  # Bases 1 e 2
make run-lenad   # Base 3 — LENAD III
make benchmark   # Desempenho de BFS e DFS
```

## Resultados gerados

Os resultados são organizados nas pastas dentro de `outputs/`:

- **`outputs/questionario/`**: grafo, métricas e visualizações da Base 1.
- **`outputs/divulgacao_youtube_instagram/`**: estrutura do grafo, tabelas de vértices e arestas, resultados da BFS e rankings da Base 2.
- **`outputs/lenad/`**: gráficos estatísticos da Base 3.
- **`outputs/desempenho/`**: resultados dos experimentos de desempenho.
 
As visualizações finais organizadas no Gephi são mantidas diretamente na pasta `outputs/`:

- `outputs/grafo_gephi.png`: visualização da Base 1.
- `outputs/grafo_apostas2.pdf`: visualização da Base 2.

O script da Base 2 exporta a estrutura e os atributos do grafo, sem gerar uma segunda imagem dessa visualização.

## Metodologia e limitações

- A pesquisa por questionário utiliza amostra por conveniência. Seus resultados descrevem os respondentes e não devem ser apresentados como estimativas representativas de toda a população brasileira.
- As arestas do questionário representam respostas de exposição informadas pelos participantes. Não comprovam, isoladamente, influência causal nem caminhos reais de disseminação.
- Na Base 2, os registros correspondem ao material coletado e classificado, não ao universo completo de publicações de cada rede social.
- As datas da Base 2 correspondem às datas de publicação registradas na coleta.
- Diferenças na quantidade de registros identificados entre YouTube e Instagram não devem ser interpretadas isoladamente como diferenças na quantidade real de publicidade em cada rede.
- As bases possuem unidades de análise diferentes e devem ser interpretadas separadamente.
- O PGSI é um instrumento de rastreamento e classificação de risco, não um diagnóstico clínico. Os denominadores podem variar entre tabelas, itens podem se sobrepor e associações observadas não demonstram causalidade.

## Reprodutibilidade

Os dados de entrada não são versionados neste repositório. Para executar as análises, mantenha os arquivos necessários na pasta local `data/`, conforme os nomes e formatos esperados pelos scripts.

Consulte o código e a documentação do depósito no Zenodo para compreender a origem, o tratamento e as limitações dos dados disponibilizados publicamente.