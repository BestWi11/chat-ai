# SQL e Python para Engenharia de Dados

## SQL Avançado para Análise e Engenharia
O SQL é a linguagem universal de consulta e manipulação de dados. Para pipelines robustos e análises complexas, o domínio de recursos avançados é indispensável:

### Window Functions (Funções de Janela)
Diferente das agregações com `GROUP BY`, as Window Functions calculam métricas sobre um conjunto de linhas (janela) sem reduzir o número de linhas retornadas.
- `ROW_NUMBER() OVER (PARTITION BY cliente_id ORDER BY data_compra DESC)`: Atribui um índice sequencial único por partição; é a técnica padrão para desduplicação de registros.
- `RANK()` e `DENSE_RANK()`: Classificam valores atribuindo empates com ou sem lacunas no ranking.
- `LAG(valor, 1)` e `LEAD(valor, 1)`: Acessam o valor da linha anterior ou posterior dentro da partição, facilitando o cálculo de taxas de crescimento (MoM, YoY) e intervalos entre eventos.

### CTEs (Common Table Expressions)
Definidas pela cláusula `WITH nome_cte AS (...)`, as CTEs permitem modularizar consultas extensas em etapas lógicas legíveis, substituindo subqueries aninhadas e permitindo recursão quando necessário.

### Otimização de Consultas SQL
- Evitar `SELECT *` e projetar apenas as colunas estritamente necessárias para economizar I/O e memória.
- Filtrar dados nas primeiras etapas (`WHERE`) antes de efetuar junções pesadas (`JOIN`).
- Analisar o plano de execução (`EXPLAIN` / `EXPLAIN COST`) para identificar gargalos como varreduras completas de tabela (Full Table Scans) ou re-shuffling de dados excessivo.

## Python para Dados: Pandas, Polars e PySpark

### Comparativo de Ferramentas
- **Pandas:** Excelente para exploração interativa de datasets pequenos a médios que cabem na memória RAM de uma única máquina. Fácil de usar, com rica comunidade e suporte a praticamente qualquer formato de dados.
- **Polars:** Biblioteca de DataFrames moderna escrita em Rust, focada em altíssimo desempenho e uso eficiente de múltiplos núcleos de CPU via multithreading nativo e avaliação preguiçosa (LazyFrames).
- **PySpark:** A API Python para o Apache Spark, projetada para computação distribuída em escala de Big Data (terabytes ou petabytes), dividindo os dados em partições e processando em clusters de nós computacionais.

## Apache Spark e PySpark: Transformações Narrow vs Wide
No ecossistema Apache Spark e PySpark para processamento distribuído, as transformações dividem-se em dois grupos fundamentais que determinam a performance do cluster:
- **Transformações Narrow (Estreitas):** Cada partição de saída depende diretamente de dados de apenas uma partição de entrada (exemplos: `filter()`, `select()`, `withColumn()`). Não exigem movimentação de dados pela rede (sem shuffle), executando de forma rápida e com baixo custo computacional.
- **Transformações Wide (Amplas):** Exigem a redistribuição e reorganização física de dados entre múltiplos nós executores do cluster através da operação de **Shuffle** (exemplos: `groupBy()`, `join()`, `distinct()`, `orderBy()`). O shuffle é o maior gargalo de desempenho em jobs de Big Data.
- **Otimização via Broadcast Joins:** Técnica que transmite integralmente tabelas dimensionais pequenas para todos os nós do cluster, transformando uma junção ampla (Wide) em uma junção estreita (Narrow) e eliminando o shuffle da tabela fato massiva.

