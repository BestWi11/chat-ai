"""Testes unitários para o gerador de embeddings locais."""

import pytest
import numpy as np
from src.rag.embedder import get_embedder, LocalEmbedder


def test_embedder_dimension():
    """Testa se o vetor gerado possui exatamente 384 dimensões."""
    embedder = get_embedder()
    vector = embedder.embed_text("O que é Engenharia de Dados?")
    
    assert isinstance(vector, list)
    assert len(vector) == LocalEmbedder.EMBEDDING_DIM
    assert all(isinstance(v, float) for v in vector)


def test_embedder_batch():
    """Testa geração de embeddings em lote."""
    embedder = get_embedder()
    texts = [
        "Primeiro texto para teste.",
        "Segundo texto sobre RAG e bancos vetoriais.",
        "Terceiro texto sobre pipelines de dados."
    ]
    vectors = embedder.embed_batch(texts)
    
    assert len(vectors) == 3
    for v in vectors:
        assert len(v) == 384


def test_semantic_similarity():
    """
    Testa se textos semanticamente próximos possuem maior similaridade
    de cosseno do que textos sobre assuntos totalmente diferentes.
    """
    embedder = get_embedder()
    
    t1 = "Como fazer deploy da aplicação no Hugging Face Spaces?"
    t2 = "Publicando o assistente de inteligência artificial no Hugging Face"
    t3 = "Receita caseira de bolo de chocolate e morango"
    
    v1 = np.array(embedder.embed_text(t1))
    v2 = np.array(embedder.embed_text(t2))
    v3 = np.array(embedder.embed_text(t3))
    
    # Como os vetores são normalizados, o produto escalar é a similaridade de cosseno
    sim_t1_t2 = float(np.dot(v1, v2))
    sim_t1_t3 = float(np.dot(v1, v3))
    
    # A similaridade entre os tópicos relacionados deve ser muito maior
    assert sim_t1_t2 > sim_t1_t3
    assert sim_t1_t2 > 0.60
    assert sim_t1_t3 < 0.40
