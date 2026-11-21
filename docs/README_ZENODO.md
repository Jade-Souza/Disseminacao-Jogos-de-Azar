# Dados agregados — Disseminação dos Jogos de Azar Online no Brasil

## Sobre este depósito

Este depósito reúne versões agregadas de duas bases utilizadas na pesquisa acadêmica **“Disseminação dos Jogos de Azar Online no Brasil: Uma Análise das Redes de Influência por Meio da Teoria dos Grafos”**.

Os arquivos disponibilizados não contêm respostas individuais do questionário nem identificadores, nomes ou links de perfis e publicações da coleta de redes sociais. A Base 3 (LENAD III) não faz parte deste depósito.

## Arquivos

### `base1_frequencia_canais.csv` — Base 1: questionário

Apresenta a quantidade e o percentual de participantes que mencionaram cada canal de contato com conteúdos relacionados a jogos de azar online.

- Unidade apresentada: categoria de canal.
- Denominador dos percentuais: total de participantes do questionário.
- Respostas individuais e combinações de canais por participante não são disponibilizadas.
- Como cada participante pode mencionar mais de um canal, os percentuais não precisam somar 100%.

O arquivo permite consultar as frequências descritivas, mas não reconstruir a lista individual de arestas do grafo bipartido nem repetir as buscas BFS e DFS sobre o grafo original.

### `base2_frequencia_plataformas_por_rede.csv` — Base 2: YouTube e Instagram

Apresenta contagens agregadas por rede social e plataforma de apostas identificada, incluindo a categoria “Não identificada”.

- `rede_social`: rede social do registro.
- `plataforma`: plataforma identificada ou “Não identificada”.
- `quantidade_registros`: número de registros da coleta naquela combinação.
- `quantidade_perfis_distintos`: número de perfis distintos associados àquela combinação.

A contagem de perfis distintos é feita usando o campo `ID` da base de trabalho, que funciona como identificador interno de cada perfil. O ID é utilizado somente durante o cálculo e não aparece no arquivo agregado. A rotina valida que cada ID corresponda a um único nome de perfil e a uma única rede social.

Não são disponibilizados nomes de perfis, links de canais, títulos, links de vídeos/publicações ou descrições textuais individuais.

Como os dados foram agregados por rede e plataforma, este arquivo permite reproduzir as frequências descritivas, mas não reconstruir a rede dirigida perfil–plataforma nem repetir a BFS do grafo original.

## Método de preparação

Os arquivos agregados são gerados a partir dos arquivos de trabalho do projeto pelo script `preparar_zenodo.py`, disponível no repositório do projeto.

Na Base 1, as respostas de canais são separadas, padronizadas e contabilizadas por categoria. Na Base 2, os registros são agrupados por rede social e plataforma, contando-se os IDs internos distintos em cada grupo, sem exportar esses identificadores.

## Limitações

As bases refletem os participantes e os conteúdos observados durante a pesquisa. Não constituem amostras probabilísticas representativas da população brasileira nem um levantamento exaustivo de todas as publicações das plataformas.

Na Base 1, as frequências são descritivas e não permitem inferir causalidade. Na Base 2, diferenças entre redes podem refletir também diferenças de coleta, disponibilidade e identificação das plataformas nos conteúdos observados.

## Código e reprodutibilidade

O código-fonte das análises está disponível no repositório:

https://github.com/Jade-Souza/Disseminacao-Jogos-de-Azar

Os arquivos deste depósito são versões agregadas para compartilhamento público. Eles não substituem os arquivos de trabalho utilizados para gerar os grafos completos.

## Citação

Ao utilizar estes dados, cite o registro do Zenodo pelo DOI atribuído após a publicação e cite também o trabalho acadêmico correspondente, quando disponível.
