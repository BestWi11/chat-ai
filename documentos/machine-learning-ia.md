# Machine Learning, MLOps e Inteligência Artificial

## Fundamentos de Machine Learning
Machine Learning (Aprendizado de Máquina) é a disciplina da Inteligência Artificial que desenvolve algoritmos capazes de aprender padrões a partir de dados históricos para realizar previsões ou tomar decisões sem serem explicitamente programados com regras fixas.

### Aprendizado Supervisionado vs Não Supervisionado
- **Supervisionado:** O modelo aprende a partir de dados rotulados, onde cada exemplo possui entradas (features) e a resposta correta esperada (target).
  - *Classificação:* Previsão de categorias discretas (ex.: detectar se uma transação bancária é fraudulenta ou legítima, diagnóstico médico).
  - *Regressão:* Previsão de valores numéricos contínuos (ex.: estimativa de faturamento de vendas, previsão de temperatura).
- **Não Supervisionado:** O modelo busca padrões intrínsecos e estruturas ocultas em dados não rotulados.
  - *Clusterização (Agrupamento):* Segmentação de clientes com comportamentos de compra semelhantes (ex.: K-Means).
  - *Redução de Dimensionalidade:* Compressão de centenas de variáveis em componentes principais (PCA, t-SNE) para visualização e redução de ruído.

## O Dilema Viés-Variância: Overfitting e Underfitting
- **Underfitting (Alto Viés):** O modelo é simples demais para capturar os padrões subjacentes dos dados, apresentando baixo desempenho tanto no treino quanto no teste.
- **Overfitting (Alta Variância):** O modelo memoriza detalhes e ruídos do conjunto de treinamento, obtendo acurácia artificialmente alta no treino, mas falhando miseravelmente ao generalizar para novos dados de teste.
- **Estratégias de Mitigação:**
  - Validação Cruzada (K-Fold Cross-Validation);
  - Técnicas de Regularização (L1 Lasso, L2 Ridge, Dropout em redes neurais);
  - Aumento de dados (Data Augmentation) e simplificação do modelo (poda de árvores, limitação de profundidade máxima).

## Métricas de Avaliação Essenciais
- **Acurácia:** Proporção de acertos totais. Pode ser enganosa em datasets desbalanceados (ex.: 99% de transações normais e 1% de fraudes).
- **Precisão (Precision):** Dentre todos os exemplos que o modelo classificou como positivos, quantos eram de fato positivos? (Crucial quando o custo do falso positivo é alto, ex.: filtro de spam).
- **Revocação (Recall / Sensibilidade):** Dentre todos os exemplos verdadeiramente positivos, quantos o modelo conseguiu identificar? (Crucial quando o falso negativo é perigoso, ex.: diagnóstico de doenças graves ou detecção de fraudes).
- **F1-Score:** Média harmônica entre Precisão e Revocação, oferecendo um balanço equilibrado.
- **ROC-AUC:** Mede a capacidade do modelo de distinguir entre classes em diferentes pontos de corte de probabilidade.
- **RMSE e MAE:** Métricas padrão para regressão, medindo a magnitude média dos erros de previsão.

## MLOps: Engenharia de Machine Learning em Produção
MLOps (Machine Learning Operations) é a aplicação de princípios de DevOps para o ciclo de vida completo de modelos de IA:
- **Versionamento com MLflow:** Rastreamento de parâmetros, código, métricas e artefatos de modelos treinados para garantir reproducibilidade.
- **Feature Store:** Repositório centralizado de variáveis calculadas, garantindo que as mesmas features usadas no treinamento sejam servidas durante a inferência em tempo real, evitando o descompasso entre treino e serviço (Training-Serving Skew).
- **Monitoramento Contínuo:** Acompanhamento de degradação do modelo ao longo do tempo causada por **Data Drift** (mudança na distribuição das features de entrada) e **Concept Drift** (mudança na relação estatística entre as features e o target de negócio).
