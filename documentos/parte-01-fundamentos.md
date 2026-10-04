# Apostila Parte 1: Fundamentos do Chat-IA e Deploy Contínuo

## Introdução ao Projeto
O Chat-IA Personalizado é um assistente conversacional inteligente projetado com propósito pedagógico para estudantes de tecnologia, Engenharia de Dados e Inteligência Artificial. O objetivo é tirar dúvidas de forma didática, como um professor paciente e acessível.

## Arquitetura do Assistente
O assistente é construído utilizando Python e o framework Gradio para a interface web. Ele não armazena dados de navegação de forma permanente (stateless), rodando de forma leve em hardware de CPU básica. A comunicação com o usuário é feita através de streaming de texto em tempo real, gerando a sensação de digitação imediata.

## Contrato do config.yaml
Todas as personalizações do assistente são feitas através de um único arquivo central chamado `config.yaml` localizado na raiz do projeto. Nesse arquivo, é possível alterar:
- O nome do assistente e a descrição do cabeçalho;
- A identidade visual, incluindo cor primária, cor secundária, cor de fundo e logotipo;
- A ordem de preferência dos provedores e modelos de IA;
- O papel pedagógico (System Prompt), tom de voz e regras de conduta;
- As perguntas de exemplo que aparecem como botões clicáveis para o aluno.

## Modelos de IA e Sistema de Fallback
O assistente integra múltiplos provedores através da API do OpenRouter, além de suportar OpenAI e Anthropic.
O OpenRouter é o provedor prioritário por permitir o uso de modelos gratuitos e de ponta. Quando o usuário envia uma dúvida, o assistente tenta o primeiro modelo da lista. Se o modelo falhar por sobrecarga, cota de requisições (erro 429) ou instabilidade temporária, o sistema aciona automaticamente o próximo modelo configurado sem travar a conversa do aluno.

## Segurança e Portão de Testes
Chaves de API e credenciais confidenciais nunca devem ser escritas no código ou enviadas para o repositório público do GitHub. Elas devem ficar armazenadas exclusivamente nas configurações seguras de ambiente (Variables and secrets).
Antes de qualquer publicação, um portão de qualidade automatizado (Quality Gate) verifica:
1. A sintaxe do arquivo `config.yaml`;
2. A validade de cores hexadecimais e existência do arquivo de logo;
3. Um escaneamento anti-vazamento de segredos para garantir que nenhuma chave foi commitada por engano.

## Publicação e Deploy
O código do projeto fica hospedado no GitHub e a aplicação é executada no Hugging Face Spaces.
Toda vez que uma alteração é enviada para a branch `main` do GitHub, o pipeline do GitHub Actions roda a suíte de testes. Se todas as verificações passarem, o código é sincronizado automaticamente com o Hugging Face Spaces. Se algum teste falhar, o deploy é cancelado e o assistente no ar continua funcionando normalmente sem interrupções.
