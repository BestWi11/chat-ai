"""Testes de segurança e prevenção contra vazamento de segredos."""

from validate_config import check_for_secret_leaks, SECRET_PATTERNS
import tempfile
import os


def test_no_secrets_in_repo():
    """Garante que nenhum arquivo do repositório contém chaves de API commitadas."""
    leaks = check_for_secret_leaks(".")
    assert len(leaks) == 0, f"Chaves detectadas no repositório: {leaks}"


def test_leak_detector_catches_fake_keys(tmp_path):
    """Testa se o detector de vazamento identifica chaves de teste."""
    dummy_file = tmp_path / "leak.py"
    # Monta a chave dinamicamente para não disparar falso positivo no próprio arquivo de teste
    fake_key = "sk-or-" + "v1-" + "abcdef1234567890abcdef1234567890"
    dummy_file.write_text(f"API_KEY = '{fake_key}'\n", encoding="utf-8")

    leaks = check_for_secret_leaks(str(tmp_path))
    assert len(leaks) >= 1
    assert "OpenRouter" in leaks[0]
