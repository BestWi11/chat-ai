"""Testes unitários e de integração para o SupabaseRetriever."""

import os
import pytest
from unittest.mock import MagicMock
from src.rag.retriever import SupabaseRetriever, SearchResult, normalize_supabase_url


def test_normalize_supabase_url():
    """Testa normalização e limpeza de URLs do Supabase."""
    assert normalize_supabase_url("https://meu-projeto.supabase.co/") == "https://meu-projeto.supabase.co"
    assert normalize_supabase_url("https://meu-projeto.supabase.co/rest/v1/") == "https://meu-projeto.supabase.co"
    assert normalize_supabase_url(" https://meu-projeto.supabase.co/rest/v1 ") == "https://meu-projeto.supabase.co"


def test_retriever_unconfigured_fallback():
    """Testa se o retriever retorna lista vazia quando não há credenciais."""
    retriever = SupabaseRetriever(supabase_url="", supabase_key="")
    assert not retriever.is_configured()
    assert retriever.get_active_version() == "v1"
    assert retriever.search("Dúvida qualquer") == []


def test_retriever_active_version_with_mock():
    """Testa leitura da versão ativa a partir do mock do cliente Postgrest."""
    retriever = SupabaseRetriever(supabase_url="https://mock.supabase.co", supabase_key="fake-key")
    
    mock_postgrest = MagicMock()
    mock_postgrest.from_().select().eq().execute.return_value = MagicMock(
        data=[{"active_version": "commit-abc1234"}]
    )
    retriever._client = mock_postgrest

    version = retriever.get_active_version()
    assert version == "commit-abc1234"


def test_retriever_search_filters_score():
    """Testa conversão dos resultados RPC para SearchResult e filtro por min_score."""
    retriever = SupabaseRetriever(supabase_url="https://mock.supabase.co", supabase_key="fake-key")
    
    mock_postgrest = MagicMock()
    mock_postgrest.from_().select().eq().execute.return_value = MagicMock(data=[{"active_version": "v1"}])
    mock_postgrest.rpc().execute.return_value = MagicMock(
        data=[
            {
                "id": 1,
                "document_name": "doc1.md",
                "section_title": "Secao 1",
                "content": "Conteudo relevante",
                "final_score": 0.025
            },
            {
                "id": 2,
                "document_name": "doc2.md",
                "section_title": "Secao 2",
                "content": "Conteudo pouco relevante",
                "final_score": 0.010  # Abaixo do default min_score (0.015)
            }
        ]
    )
    retriever._client = mock_postgrest

    results = retriever.search("teste", min_score=0.015)
    assert len(results) == 1
    assert isinstance(results[0], SearchResult)
    assert results[0].document_name == "doc1.md"
    assert results[0].final_score == 0.025


def test_live_supabase_connection_if_configured():
    """Se as credenciais reais estiverem no ambiente, testa a consulta ao vivo."""
    retriever = SupabaseRetriever()
    if retriever.is_configured():
        version = retriever.get_active_version()
        assert isinstance(version, str)
        assert len(version) > 0

        # Testa busca RPC real (retornará lista vazia caso não haja chunks indexados ainda)
        results = retriever.search("O que é Data Lake?", top_k=3)
        assert isinstance(results, list)
