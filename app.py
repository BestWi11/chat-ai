"""
Ponto de entrada da aplicação (Entrypoint).
Compatível com execução local e Hugging Face Spaces (Porta 7860).
"""

import sys
from src.config_loader import load_config, ConfigValidationError
from src.ui import create_ui


def main():
    try:
        config = load_config("config.yaml")
        print(f"✅ Configurações carregadas com sucesso: '{config.app.title}'")
        print(f"🤖 Provedor principal: {config.llm.providers[0].name} ({config.llm.providers[0].model})")
    except ConfigValidationError as e:
        print(f"❌ Erro fatal ao carregar configurações:\n{e}", file=sys.stderr)
        sys.exit(1)

    app = create_ui(config)
    # Porta 7860 é a porta padrão exposta no Hugging Face Spaces
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        share=False
    )


if __name__ == "__main__":
    main()
