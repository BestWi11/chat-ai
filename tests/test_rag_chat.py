"""
Testes unitários para integração RAG no LLMClient e no chat.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.config_loader import load_config
from src.llm_client import LLMClient
from src.rag.retriever import SearchResult


def test_rag_chat_out_of_scope_rejection_when_web_fallback_disabled():
    """Testa se pergunta fora do material recebe resposta padrão estrita quando web_search_fallback=False."""
    config = load_config("config.yaml")
    config.rag.web_search_fallback = False
    client = LLMClient(config)

    # Simula retriever retornando lista vazia (fora do escopo / score abaixo do min)
    client.retriever = MagicMock()
    client.retriever.is_configured.return_value = True
    client.retriever.search.return_value = []

    history = [{"role": "user", "content": "Qual a capital da França e quem descobriu o Brasil?"}]
    responses = list(client.stream_chat(history))

    assert len(responses) == 1
    assert responses[0] == "Não encontrei isso no material do curso."


def test_rag_chat_out_of_scope_with_web_fallback():
    """Testa se pergunta fora do material consulta a web e anexa fontes externas."""
    config = load_config("config.yaml")
    config.rag.web_search_fallback = True
    client = LLMClient(config)

    client.retriever = MagicMock()
    client.retriever.is_configured.return_value = True
    client.retriever.search.return_value = []

    fake_web_results = [
        {"title": "PostgreSQL Docs", "href": "https://www.postgresql.org/docs/", "body": "Documentação do Postgres."}
    ]

    with patch("src.llm_client.search_web", return_value=fake_web_results):
        with patch.object(client, "_get_api_key", return_value="fake-key"):
            with patch.object(
                client,
                "_stream_openrouter_or_openai",
                return_value=iter(["PostgreSQL é um banco relacional avançado."])
            ):
                history = [{"role": "user", "content": "Como instalar PostgreSQL?"}]
                chunks = list(client.stream_chat(history))
                full_resp = "".join(chunks)

                assert "PostgreSQL é um banco relacional avançado." in full_resp
                assert "🌐 **Fontes e Recomendações Externas:**" in full_resp
                assert "https://www.postgresql.org/docs/" in full_resp



def test_rag_chat_grounded_response_with_citations():
    """Testa se pergunta fundamentada injeta contexto e anexa as fontes no rodapé."""
    config = load_config("config.yaml")
    client = LLMClient(config)

    # Simula retriever retornando chunks válidos
    client.retriever = MagicMock()
    client.retriever.is_configured.return_value = True
    client.retriever.search.return_value = [
        SearchResult(
            id=1,
            document_name="parte-02-engenharia-rag.md",
            section_title="O que é RAG",
            content="RAG significa Retrieval-Augmented Generation.",
            final_score=0.016
        )
    ]

    # Simula streaming do provedor retornando resposta
    with patch.object(client, "_get_api_key", return_value="fake-key"):
        with patch.object(
            client,
            "_stream_openrouter_or_openai",
            return_value=iter(["RAG é ", "Retrieval-Augmented Generation."])
        ):
            history = [{"role": "user", "content": "O que é RAG?"}]
            chunks_generated = list(client.stream_chat(history))
            full_response = "".join(chunks_generated)

            assert "RAG é Retrieval-Augmented Generation." in full_response
            assert "📚 **Fontes consultadas:**" in full_response
            assert "parte-02-engenharia-rag.md" in full_response
            assert "O que é RAG" in full_response
