# Disseminação dos Jogos de Azar Online no Brasil

Projeto acadêmico que investiga a disseminação de conteúdos relacionados a jogos de azar online por meio da Teoria dos Grafos e de análise estatística descritiva.

## Organização das bases

As bases são analisadas separadamente porque representam unidades e relações diferentes:

- **Base 1 — Questionário:** grafo bipartido não dirigido entre participantes e canais de contato/exposição.
- **Base 2 — YouTube e Instagram:** grafo dirigido de três camadas, com relações entre rede social, perfil/canal e plataforma de apostas.
- **Base 3 — LENAD III:** análise estatística descritiva de indicadores e consequências relacionadas às apostas. Não é convertida em grafo.

## Estrutura do projeto

- `main.py`: ponto de entrada das análises das Bases 1 e 2.
- `src/graph_builder.py`: carrega a planilha do questionário e constrói o grafo da Base 1.
- `src/bfs.py` e `src/dfs.py`: implementações de BFS e DFS para a Base 1.
- `src/metrics.py`: métricas estruturais da Base 1.
- `src/visualization.py`: gráficos estatísticos da Base 1.
- `src/base2_analysis.py`: leitura, construção, métricas e exportação do grafo da Base 2.
- `src/base2_visualization.py`: visualizações da Base 2.
- `src/lenad_visualization.py`: gráficos estatísticos do LENAD III.
- `data/dados_originais.xlsx`: dados do questionário (Base 1).
- `data/Pasta(base_youtube_instagram).csv`: registros coletados no YouTube e Instagram (Base 2).
- `data/base_estruturada_LENAD_III.xlsx`: planilha estruturada do LENAD III (Base 3).

## Requisitos e instalação

Python 3.10 ou superior.

```bash
pip install -r requirements.txt
```

## Executar as análises

Na raiz do repositório:

```bash
# Base 1 — questionário (comportamento padrão)
python main.py

# Base 2 — YouTube e Instagram
python main.py --base 2

# Executar as duas bases
python main.py --base todas

# Somente LENAD III (Base 3)
python src/lenad_visualization.py
```

### Base 1 — Questionário

A execução gera o GEXF e os gráficos em `outputs/questionario/`. O GEXF pode ser importado no Gephi para configurar a disposição espacial, cores, tamanhos e rótulos da visualização final.

### Base 2 — YouTube e Instagram

O script lê o CSV separado por ponto e vírgula e constrói automaticamente uma rede dirigida com três camadas:

1. Rede social (YouTube ou Instagram) → perfil/canal;
2. Perfil/canal → plataforma de apostas.

O peso da aresta entre perfil e plataforma corresponde à quantidade de registros coletados para aquela relação. Registros classificados como “Não identificada” são mantidos na contagem descritiva, mas não geram um vértice genérico de plataforma. Registros repetidos não são removidos automaticamente: cada linha da base original é considerada um registro da coleta.

Os resultados são salvos em `outputs/base2/`:

- `grafo_base2.gexf`: grafo para importação e edição no Gephi;
- `vertices.csv` e `arestas.csv`: tabelas de vértices e arestas;
- `metricas.json`: métricas e resumo por rede social;
- `ranking_perfis.csv` e `ranking_plataformas.csv`: tabelas de frequência;
- `grafo_base2_python.png`: visualização geral gerada pelo Python;
- `publicacoes_por_perfil.png`, `publicacoes_por_plataforma.png` e `registros_por_rede.png`: gráficos descritivos.

O arquivo final `outputs/grafo_base2.pdf`, organizado anteriormente no Gephi, é preservado. A visualização gerada pelo Python é uma representação reprodutível de apoio e não substitui o layout final do Gephi.

**Limitação de coleta:** a identificação de plataformas depende da disponibilidade e da clareza dos conteúdos públicos observados. Conteúdos temporários, como Stories, publicações antigas indisponíveis e divulgações sem identificação explícita podem dificultar a identificação. Portanto, diferenças entre YouTube e Instagram na quantidade de registros identificados não devem ser interpretadas isoladamente como diferenças na quantidade real de publicidade ou disseminação em cada rede.

### Base 3 — LENAD III

A análise do LENAD III utiliza estatísticas agregadas publicadas no material de referência e transcritas para a planilha estruturada. Não estima relações individuais, não calcula causalidade e não trata o PGSI como diagnóstico clínico.

Para executar:

```bash
python src/lenad_visualization.py
```

Também é possível indicar outros caminhos:

```bash
python src/lenad_visualization.py --entrada caminho/da/planilha.xlsx --saida outputs
```

Os gráficos são salvos em PDF na pasta `outputs/lenad/`.

## Cuidados metodológicos

- A pesquisa por questionário utiliza amostra por conveniência; seus resultados descrevem os respondentes e não devem ser apresentados como estimativas representativas de toda a população brasileira.
- As arestas do questionário representam respostas de exposição informadas pelos participantes. Não comprovam, isoladamente, influência causal nem caminhos reais de disseminação.
- Na Base 2, os registros correspondem ao material coletado e classificado, não ao universo completo de publicações de cada rede social.
- As datas da Base 2 correspondem às datas de publicação registradas na coleta.
- As bases têm unidades de análise diferentes e devem ser interpretadas separadamente.
- O PGSI é um instrumento de rastreamento/classificação de risco, não um diagnóstico clínico. Os denominadores variam entre tabelas; itens podem se sobrepor e associações observadas não demonstram causalidade.

## Reprodutibilidade

Mantenha os dados de entrada utilizados na análise em `data/` e registre a origem, o período de coleta, os critérios de seleção e as limitações de cada base. Não remova ou deduplique registros brutos sem justificativa metodológica documentada.
