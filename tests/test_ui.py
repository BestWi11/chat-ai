"""Teste de integridade e smoke test da UI Gradio."""

from src.config_loader import load_config
from src.ui import create_ui
import gradio as gr


def test_ui_builds_without_error():
    """Testa se a árvore de componentes da UI é criada com sucesso a partir da configuração padrão."""
    config = load_config("config.yaml")
    demo = create_ui(config)
    assert isinstance(demo, gr.Blocks)
    assert demo.title == config.app.title
