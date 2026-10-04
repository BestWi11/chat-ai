"""
Testes unitários para scripts/eval_rag.py.
"""

import json
import pytest
from unittest.mock import MagicMock
from scripts.eval_rag import (
    is_matching_chunk,
    calculate_metrics,
    promote_active_version,
    run_evaluation
)
from src.rag.retriever import SearchResult


def test_is_matching_chunk_success():
    assert is_matching_chunk(
        result_doc="parte-01-fundamentos.md",
        result_section="Contrato do config.yaml",
        expected_doc="parte-01-fundamentos.md",
        expected_section="Contrato do config.yaml"
    )

    # Tolerância a case e caracteres
    assert is_matching_chunk(
        result_doc="Parte-01-Fundamentos.md",
        result_section="Contrato do config.yaml",
        expected_doc="parte-01-fundamentos.md",
        expected_section="contrato do config yaml"
    )


def test_is_matching_chunk_different_doc_fails():
    assert not is_matching_chunk(
        result_doc="parte-02-engenharia-rag.md",
        result_section="Contrato do config.yaml",
        expected_doc="parte-01-fundamentos.md",
        expected_section="Contrato do config.yaml"
    )


def test_calculate_metrics():
    sample_eval = [
        {"hit": True, "reciprocal_rank": 1.0},
        {"hit": True, "reciprocal_rank": 0.5},
        {"hit": False, "reciprocal_rank": 0.0},
        {"hit": True, "reciprocal_rank": 0.3333}
    ]
    hit_rate, mrr = calculate_metrics(sample_eval)
    assert hit_rate == 0.75  # 3 de 4
    assert pytest.approx(mrr, 0.001) == (1.0 + 0.5 + 0.0 + 0.3333) / 4


def test_promote_active_version():
    mock_client = MagicMock()
    mock_from = MagicMock()
    mock_update = MagicMock()
    mock_eq = MagicMock()

    mock_client.from_.return_value = mock_from
    mock_from.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute.return_value = MagicMock(data=[{"id": 1, "active_version": "v_test"}])

    success = promote_active_version("v_test", client=mock_client)
    assert success is True
    mock_client.from_.assert_called_with("rag_metadata")
    mock_update.eq.assert_called_with("id", 1)


def test_run_evaluation_mocked(tmp_path):
    questions_file = tmp_path / "questions.json"
    questions_file.write_text(json.dumps([
        {
            "id": "q1",
            "question": "Como configuro o config.yaml?",
            "expected_document": "parte-01-fundamentos.md",
            "expected_section": "Contrato do config.yaml"
        }
    ]), encoding="utf-8")

    mock_retriever = MagicMock()
    mock_retriever.get_active_version.return_value = "v_test"
    mock_retriever.search.return_value = [
        SearchResult(
            id=1,
            document_name="parte-01-fundamentos.md",
            section_title="Contrato do config.yaml",
            content="Instruções do config.yaml",
            final_score=0.016
        )
    ]

    report = run_evaluation(
        questions_file=str(questions_file),
        version_id="v_test",
        top_k=3,
        threshold=0.80,
        retriever=mock_retriever
    )

    assert report["passed"] is True
    assert report["hit_rate"] == 1.0
    assert report["mrr"] == 1.0
