# Databricks e Arquitetura Lakehouse

## O Conceito de Data Lakehouse
O **Data Lakehouse** é um paradigma arquitetural que unifica as melhores características do Data Lake e do Data Warehouse em uma plataforma única.
- Do **Data Lake**, ele herda a capacidade de armazenar dados brutos não estruturados, semiestruturados e estruturados em formatos abertos (como Parquet), com altíssima escalabilidade e baixo custo de armazenamento em nuvem (S3, ADLS, GCS).
- Do **Data Warehouse**, ele incorpora recursos de governança corporativa, confiabilidade, suporte a transações ACID, controle de versão (Time Travel) e altíssimo desempenho para consultas SQL e BI.

## Delta Lake e Armazenamento Confiável
O **Delta Lake** é a camada de armazenamento open-source que viabiliza o Lakehouse. Ele adiciona um log de transações baseado em JSON (`_delta_log`) sobre arquivos Parquet, trazendo vantagens fundamentais:
- **Transações ACID:** Garante que múltiplas operações de leitura e escrita simultâneas ocorram sem inconsistências ou leituras de dados parciais.
- **Time Travel:** Permite consultar versões anteriores da tabela a partir de timestamps ou números de versão (`VERSION AS OF` ou `TIMESTAMP AS OF`), facilitando auditorias, rollback de erros e reprodutibilidade de experimentos de Machine Learning.
- **Otimizações de Performance:** Recursos como `OPTIMIZE` (compactação de arquivos pequenos em tamanhos ideais) e `Z-ORDER BY` (co-localização multidimensional de dados para acelerar filtros em colunas de alta cardinalidade).
- **Schema Enforcement & Evolution:** Impede a inserção acidental de dados com tipos incompatíveis e permite a evolução controlada do esquema com `mergeSchema`.

## Arquitetura Medalhão (Medallion Architecture)
No Databricks Lakehouse, os dados são organizados e refinados progressivamente em três camadas estruturadas:
1. **Camada Bronze (Dados Brutos / Raw):**
   - É o ponto de aterrissagem (landing) dos dados exatamente como chegam das fontes externas.
   - Preserva o histórico completo, enriquecido com metadados de ingestão (data de carga, arquivo de origem).
   - O esquema permanece flexível e os dados não sofrem alterações nem filtros destrutivos.
2. **Camada Silver (Dados Limpos e Padronizados):**
   - Os dados da camada Bronze são desduplicados, validados e tipados.
   - Aplicação de regras de conformidade, padronização de datas, tratamento de valores nulos e enriquecimento via junções com tabelas dimensionais de referência.
   - Representa uma visão limpa e confiável em nível corporativo.
3. **Camada Gold (Dados Agregados para Negócio):**
   - Tabelas altamente refinadas, desnormalizadas e agregadas (visões analíticas, modelos dimensionais Star Schema).
   - Otimizadas diretamente para consumo por dashboards de BI (Power BI, Tableau), relatórios gerenciais e modelos preditivos de Machine Learning.

## Governança com Unity Catalog
O **Unity Catalog** é a solução unificada de governança do Databricks para todos os ativos de dados e IA no Lakehouse. Ele oferece:
- Gerenciamento centralizado de permissões em três níveis (`catalog.schema.table`);
- Controle de acesso granular baseado em papéis (RBAC) com suporte a mascaramento de colunas e segurança a nível de linha;
- Linhagem de dados automatizada (Lineage) de ponta a ponta, permitindo rastrear desde a fonte original até o dashboard final;
- Catálogo compartilhado para tabelas, arquivos (volumes), modelos de Machine Learning (MLflow) e funções SQL.
