"""Configuração global do pytest."""

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
