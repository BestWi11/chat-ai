# Engenharia de Dados: Pipelines, ETL e Arquitetura

## O que é um Pipeline de Dados
Um pipeline de dados é um conjunto automatizado de processos que extrai dados de múltiplas origens (bancos transacionais, APIs, arquivos de log, sensores IoT), transforma essas informações aplicando regras de negócio e limpeza, e as carrega em um destino analítico centralizado.
O objetivo primordial de um pipeline é garantir que os dados cheguem com confiabilidade, baixa latência e qualidade para alimentar relatórios de BI, modelos de Machine Learning e tomadas de decisão estratégicas.

## ETL vs ELT: Diferenças e Casos de Uso
A principal diferença entre os dois paradigmas reside no momento e no local onde a transformação dos dados ocorre:
- **ETL (Extract, Transform, Load):** Os dados são extraídos da fonte e passam por um servidor de processamento intermediário onde são limpos e estruturados antes de serem carregados no banco final. É tradicionalmente usado quando há restrições de privacidade rígidas (como mascaramento de dados sensíveis antes da persistência) ou quando o banco de destino não tem capacidade de computação elástica.
- **ELT (Extract, Load, Transform):** Os dados brutos são extraídos e carregados diretamente no Data Lake ou Data Warehouse em sua forma original. A transformação ocorre internamente no destino, aproveitando o poder computacional distribuído de modernas plataformas analíticas (como Databricks, Snowflake e BigQuery). É o modelo predominante na Engenharia de Dados moderna por oferecer maior agilidade e flexibilidade.

## Batch vs Streaming
Os dados podem trafegar por dois modos fundamentais de processamento:
- **Processamento em Lote (Batch):** Os dados são acumulados e processados periodicamente em intervalos regulares (a cada hora, diariamente ou semanalmente). É ideal para grandes volumes históricos, relatórios consolidados e conciliações contábeis.
- **Processamento em Tempo Real (Streaming):** Os dados são processados continuamente evento a evento ou em micro-lotes com latência de milissegundos ou segundos (usando tecnologias como Apache Kafka, Apache Flink e Spark Structured Streaming). É essencial para detecção de fraudes, sistemas de recomendação em tempo real e monitoramento de telemetria.

## Idempotência e Reprocessamento
Um pipeline de dados profissional deve ser estritamente **idempotente**: executar o pipeline múltiplas vezes com os mesmos dados de entrada no mesmo período deve produzir exatamente o mesmo resultado final, sem gerar registros duplicados ou estados inconsistentes.
As estratégias comuns para garantir idempotência incluem:
- Escrita particionada com sobrescrita atômica (`INSERT OVERWRITE` ou `MERGE INTO`);
- Identificadores de versão e controle transacional com logs de auditoria;
- Tratamento de chaves substitutas (surrogate keys) e chaves naturais de negócio.

## Orquestração e Observabilidade
A orquestração é o maestro do ecossistema de dados. Ferramentas de orquestração (como Apache Airflow, Prefect, Dagster e Databricks Workflows) coordenam a ordem de execução dos jobs através de DAGs (Directed Acyclic Graphs), gerenciam dependências, retentativas automáticas em caso de falha e monitoramento de SLA.
A observabilidade de dados monitora quatro pilares essenciais:
1. **Freshness (Atualidade):** Os dados estão atualizados dentro do tempo esperado?
2. **Volume:** O volume de registros recebidos está dentro da média histórica ou houve perda de dados?
3. **Schema:** A estrutura das colunas mudou de forma inesperada (schema drift)?
4. **Distribution:** A distribuição estatística e os valores nulos continuam normais?
