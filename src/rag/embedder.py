"""
Módulo de Geração de Embeddings Locais (384 dimensões).
Utiliza SentenceTransformers com o modelo multilíngue local na CPU, sem necessidade de chaves de API.
"""

from typing import List, Optional
import numpy as np


class LocalEmbedder:
    """Gerador de Embeddings local com carregamento em memória no padrão Singleton."""

    _instance: Optional["LocalEmbedder"] = None
    _model = None

    DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM = 384

    def __new__(cls, model_name: str = DEFAULT_MODEL_NAME):
        if cls._instance is None:
            cls._instance = super(LocalEmbedder, cls).__new__(cls)
            cls._instance.model_name = model_name
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Carrega o modelo SentenceTransformer na memória."""
        from sentence_transformers import SentenceTransformer
        # Carrega o modelo na CPU de forma otimizada
        self._model = SentenceTransformer(self.model_name, device="cpu")

    def embed_text(self, text: str) -> List[float]:
        """
        Gera o vetor de embedding (384 dimensões) normalizado para um único texto.
        """
        cleaned = text.strip()
        if not cleaned:
            return [0.0] * self.EMBEDDING_DIM

        # normalize_embeddings=True garante similaridade de cosseno via produto escalar
        embedding = self._model.encode(cleaned, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Gera vetores de embeddings em lote para otimizar a indexação de múltiplos trechos.
        """
        if not texts:
            return []

        cleaned_texts = [t.strip() if t.strip() else " " for t in texts]
        embeddings = self._model.encode(
            cleaned_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embeddings.tolist()


def get_embedder(model_name: str = LocalEmbedder.DEFAULT_MODEL_NAME) -> LocalEmbedder:
    """Função utilitária para obter a instância única do embedder."""
    return LocalEmbedder(model_name=model_name)
