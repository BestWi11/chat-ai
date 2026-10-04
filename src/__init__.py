"""Módulo principal da aplicação Chat-AI."""

# Compatibilidade entre huggingface_hub v1+ e Gradio 4.x
try:
    import huggingface_hub
    if not hasattr(huggingface_hub, "HfFolder"):
        class HfFolder:
            @staticmethod
            def get_token():
                import os
                return os.getenv("HF_TOKEN")
        huggingface_hub.HfFolder = HfFolder
except Exception:
    pass
