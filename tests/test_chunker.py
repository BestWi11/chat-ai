"""Testes unitários para o fatiador de Markdown (Chunker)."""

import pytest
from src.rag.chunker import (
    split_markdown_by_headings,
    slice_text_into_chunks,
    chunk_markdown,
    load_and_chunk_documents,
    DocumentChunk
)


SAMPLE_MARKDOWN = """# Título Principal

Texto de introdução ao documento.

## Primeira Seção
Este é o conteúdo da primeira seção. Ele contém explicações detalhadas sobre engenharia de dados.

## Segunda Seção
Este é o conteúdo da segunda seção. Ele fala sobre banco de dados vetorial e embeddings.
"""


def test_split_markdown_by_headings():
    """Testa divisão por títulos de seção Markdown."""
    sections = split_markdown_by_headings(SAMPLE_MARKDOWN)
    assert len(sections) == 3
    assert sections[0][0] == "Título Principal"
    assert sections[1][0] == "Primeira Seção"
    assert sections[2][0] == "Segunda Seção"


def test_slice_text_into_chunks_small_text():
    """Testa texto menor que o chunk_size."""
    text = "Este é um texto curto que cabe em um único trecho."
    chunks = slice_text_into_chunks(text, chunk_size=200, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_slice_text_into_chunks_large_text():
    """Testa texto maior que chunk_size gerando múltiplos trechos com overlap."""
    long_text = "Palavra " * 100  # ~800 caracteres
    chunks = slice_text_into_chunks(long_text, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 350  # Margem segura por quebra em espaço


def test_chunk_markdown_output():
    """Testa se chunk_markdown gera instâncias válidas de DocumentChunk."""
    chunks = chunk_markdown(SAMPLE_MARKDOWN, document_name="teste.md", chunk_size=300, chunk_overlap=30)
    assert len(chunks) >= 3
    for idx, c in enumerate(chunks):
        assert isinstance(c, DocumentChunk)
        assert c.document_name == "teste.md"
        assert c.chunk_index == idx
        assert c.section_title != ""
        assert len(c.content) > 0


def test_load_and_chunk_documents():
    """Testa leitura da pasta documentos/ real do repositório."""
    chunks = load_and_chunk_documents("documentos", chunk_size=500, chunk_overlap=50)
    assert len(chunks) > 0

    doc_names = {c.document_name for c in chunks}
    assert "parte-01-fundamentos.md" in doc_names
    assert "parte-02-engenharia-rag.md" in doc_names

    # Confere que os índices são ordenados e contínuos
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
