---
title: Professor IA - Engenharia de Dados & IA
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🎓 Professor IA — Engenharia de Dados & IA

Assistente conversacional didático construído para auxiliar estudantes e entusiastas em dúvidas sobre **Engenharia de Dados**, **Pipelines**, **SQL**, **Python** e **Inteligência Artificial**.

---

## 🚀 Como Funciona

- **100% Personalizável via `config.yaml`**: Altere o nome, descrição, cores, prompt pedagógico, perguntas sugeridas e modelos de IA sem mexer no código.
- **Resiliência Multi-Provedor com Fallback**: Conecta prioritariamente ao **OpenRouter** (modelo gratuito `meta-llama/llama-3.3-70b-instruct:free`) e possui fallback automático para OpenAI e Anthropic.
- **Portão de Testes Automatizado (CI/CD)**: Toda alteração enviada ao GitHub é testada e validada antes de ser publicada no Hugging Face Spaces.

---

## 🛠️ Como Rodar Localmente

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/BestWi11/chat-ai.git
   cd chat-ai
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # No Linux/macOS
   # ou: .venv\Scripts\activate no Windows
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure suas chaves no arquivo `.env`:**
   ```bash
   cp .env.example .env
   # Edite o arquivo .env e coloque sua chave OPENROUTER_API_KEY
   ```

5. **Execute a validação e inicie o chat:**
   ```bash
   python validate_config.py
   python app.py
   ```
   Acesse no navegador em: `http://localhost:7860`

---

## 🧪 Rodando os Testes

```bash
pytest -v
```

---

## 📄 Licença

Distribuído sob a licença MIT. Consulte `LICENSE` para mais detalhes.
