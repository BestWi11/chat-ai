"""
Testes unitários para o módulo src/rag/web_searcher.py.
"""

from unittest.mock import MagicMock, patch
from src.rag.web_searcher import search_web


def test_search_web_empty_query():
    assert search_web("") == []
    assert search_web("   ") == []


def test_search_web_mocked():
    mock_ddgs_instance = MagicMock()
    mock_ddgs_instance.text.return_value = [
        {"title": "Python Docs", "href": "https://docs.python.org", "body": "Documentação oficial do Python."}
    ]

    with patch("src.rag.web_searcher.DDGS", create=True) as mock_cls:
        mock_cls.return_value.__enter__.return_value = mock_ddgs_instance
        results = search_web("Python tutorial", max_results=1)

        assert len(results) == 1
        assert results[0]["title"] == "Python Docs"
        assert results[0]["href"] == "https://docs.python.org"
