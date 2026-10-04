"""
Ponto de entrada da aplicação (Entrypoint).
Compatível com execução local e Hugging Face Spaces (Porta 7860).
"""

import sys

# Patch de compatibilidade entre Pydantic v2.10+ (boolean additionalProperties) e Gradio 4
try:
    import gradio_client.utils
    _orig_schema = gradio_client.utils._json_schema_to_python_type
    def _safe_schema(schema, defs=None):
        if isinstance(schema, bool):
            return "Any"
        return _orig_schema(schema, defs)
    gradio_client.utils._json_schema_to_python_type = _safe_schema
except Exception:
    pass

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
        share=True
    )


if __name__ == "__main__":
    main()
