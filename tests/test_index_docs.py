"""
Testes unitários e de integração para scripts/index_docs.py.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from scripts.index_docs import (
    get_git_version,
    normalize_supabase_url,
    get_supabase_client,
    index_documents
)


def test_get_git_version_format():
    version = get_git_version()
    assert isinstance(version, str)
    assert version.startswith("v_")
    assert len(version) > 2


def test_normalize_supabase_url():
    assert normalize_supabase_url("https://xyz.supabase.co") == "https://xyz.supabase.co/rest/v1"
    assert normalize_supabase_url("https://xyz.supabase.co/") == "https://xyz.supabase.co/rest/v1"
    assert normalize_supabase_url("https://xyz.supabase.co/rest/v1") == "https://xyz.supabase.co/rest/v1"


def test_get_supabase_client_none_when_empty():
    client = get_supabase_client(supabase_url="", service_role_key="")
    assert client is None


def test_index_documents_missing_dir_raises():
    with pytest.raises(FileNotFoundError):
        index_documents(docs_dir="caminho_inexistente_12345")


def test_index_documents_with_mocked_supabase(tmp_path):
    # Cria documento temporário
    doc = tmp_path / "teste.md"
    doc.write_text("# Seção 1\nEste é um texto de teste para indexação RAG.", encoding="utf-8")

    mock_client = MagicMock()
    mock_from = MagicMock()
    mock_delete = MagicMock()
    mock_eq = MagicMock()
    mock_insert = MagicMock()

    mock_client.from_.return_value = mock_from
    mock_from.delete.return_value = mock_delete
    mock_delete.eq.return_value = mock_eq
    mock_eq.execute.return_value = MagicMock(data=[])

    mock_from.insert.return_value = mock_insert
    mock_insert.execute.return_value = MagicMock(data=[{"id": 1}])

    result = index_documents(
        docs_dir=str(tmp_path),
        version_id="v_test_mock",
        chunk_size=500,
        chunk_overlap=50,
        batch_size=10,
        clean_existing=True,
        client=mock_client
    )

    assert result["status"] == "success"
    assert result["version_id"] == "v_test_mock"
    assert result["docs_count"] == 1
    assert result["chunks_count"] >= 1
    mock_client.from_.assert_any_call("document_chunks")
