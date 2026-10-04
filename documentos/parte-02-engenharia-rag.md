# Apostila Parte 2: Engenharia de Dados, RAG e Busca Híbrida

## O que é RAG
RAG significa Retrieval-Augmented Generation (Geração Aumentada por Recuperação). É uma técnica que permite ao modelo de Inteligência Artificial consultar documentos externos antes de gerar uma resposta. Em vez de responder apenas com base no que foi memorizado durante seu treinamento, o assistente busca trechos relevantes nos materiais do curso e utiliza essas informações como fonte da verdade, eliminando alucinações e garantindo respostas precisas.

## Arquiteturas de Dados
Na Engenharia de Dados moderna, existem duas estruturas fundamentais de armazenamento:
- **Data Lake:** Repositório que armazena grandes volumes de dados brutos em seus formatos nativos (estruturados, semiestruturados ou não estruturados, como JSON, Parquet e arquivos de texto). Oferece alta escalabilidade e baixo custo de armazenamento.
- **Data Warehouse:** Banco de dados relacional otimizado para análise de dados estruturados e consultas SQL de alta performance (OLAP). Os dados são transformados e limpos antes de serem carregados, seguindo esquemas rígidos (como Star Schema ou Snowflake Schema).

## Fatiamento de Documentos e Chunking
Como os modelos de linguagem possuem limites de contexto e a busca vetorial funciona melhor com passagens concisas, os documentos do curso são fatiados em trechos menores chamados **chunks**.
O chunking ideal preserva o contexto semântico, respeita os títulos das seções Markdown e mantém uma sobreposição (overlap) entre trechos consecutivos para que conceitos que fiquem na borda da quebra não sejam perdidos.

## Embeddings Vetoriais
Embeddings são representações matemáticas densas do significado de um texto em um espaço multidimensional. Frases ou trechos que tratam do mesmo assunto ficam posicionados próximos nesse espaço vetorial, mesmo que utilizem palavras ou sinônimos completamente diferentes. No nosso assistente, usamos um modelo multilíngue local de 384 dimensões que roda na CPU sem custo de API.

## Banco Vetorial Supabase e pgvector
Para persistir e consultar milhões de vetores de forma eficiente, usamos o Supabase, que integra a extensão `pgvector` sobre o PostgreSQL. Ele permite combinar filtros relacionais SQL tradicionais com buscas de similaridade de cosseno de altíssima velocidade através de índices HNSW (Hierarchical Navigable Small World).

## Busca Híbrida e RRF
A busca puramente semântica (vetores) pode falhar em consultas que exigem precisão exata de termos técnicos ou códigos, enquanto a busca por texto pleno (Full-Text Search com tsvector) ignora sinônimos.
A **Busca Híbrida** combina o melhor dos dois mundos. Ela executa a busca por texto e a busca vetorial em paralelo e funde os resultados utilizando o algoritmo **RRF (Reciprocal Rank Fusion)**, atribuindo pesos equilibrados e gerando um ranking final unificado.

## Avaliação e Portão de Qualidade da Busca
Para garantir que a base de conhecimento continua precisa a cada atualização de documentos, a esteira de CI/CD roda uma bateria de perguntas de teste antes da publicação e avalia duas métricas fundamentais:
- **Hit Rate@K:** Percentual de perguntas em que o trecho correto do material foi encontrado entre os top-K resultados.
- **MRR (Mean Reciprocal Rank):** Mede a agilidade do algoritmo, calculando a média do inverso da posição em que o primeiro trecho correto apareceu. Se o Hit Rate@3 for menor que 80%, o novo índice é rejeitado e o assistente no ar continua usando a versão estável anterior.
