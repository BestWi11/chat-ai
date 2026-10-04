"""Testes automatizados para validação do config.yaml e do config_loader."""

import pytest
import tempfile
import os
from src.config_loader import load_config, ConfigValidationError, AssistantConfig


def test_load_valid_default_config():
    """Testa se o config.yaml padrão do repositório é 100% válido."""
    config = load_config("config.yaml")
    assert isinstance(config, AssistantConfig)
    assert config.app.title != ""
    assert len(config.llm.providers) >= 1
    assert config.llm.providers[0].name in ["openrouter", "openai", "anthropic"]
    assert config.theme.primary_color.startswith("#")


def test_invalid_yaml_syntax(tmp_path):
    """Testa erro de sintaxe YAML inválida."""
    bad_file = tmp_path / "bad_syntax.yaml"
    bad_file.write_text("app:\n  title: [unclosed list", encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(bad_file))
    assert "Erro de sintaxe" in str(exc.value)


def test_missing_required_fields(tmp_path):
    """Testa rejeição de configuração sem campos obrigatórios."""
    incomplete_file = tmp_path / "incomplete.yaml"
    incomplete_file.write_text("theme:\n  primary_color: '#1E3A8A'\n", encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(incomplete_file))
    assert "Falha na validação" in str(exc.value)


def test_invalid_hex_color(tmp_path):
    """Testa rejeição de cores fora do padrão hexadecimal."""
    invalid_color_file = tmp_path / "invalid_color.yaml"
    content = """
app:
  title: "Teste"
  description: "Desc"
theme:
  primary_color: "azul-escuro"
llm:
  providers:
    - name: "openrouter"
      model: "test-model"
system_prompt:
  role: "Professor de teste"
  tone: "Didático"
"""
    invalid_color_file.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(invalid_color_file))
    assert "não é um código hexadecimal válido" in str(exc.value)


def test_invalid_provider_name(tmp_path):
    """Testa rejeição de provedores não suportados."""
    invalid_prov_file = tmp_path / "invalid_provider.yaml"
    content = """
app:
  title: "Teste"
  description: "Desc"
theme:
  primary_color: "#123456"
llm:
  providers:
    - name: "gemini_invalido"
      model: "gemini-pro"
system_prompt:
  role: "Professor de teste"
  tone: "Didático"
"""
    invalid_prov_file.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(invalid_prov_file))
    assert "Provedor 'gemini_invalido' inválido" in str(exc.value)


def test_missing_logo_file(tmp_path):
    """Testa erro caso o caminho do logo aponte para arquivo inexistente."""
    missing_logo_file = tmp_path / "missing_logo.yaml"
    content = """
app:
  title: "Teste"
  description: "Desc"
  logo_path: "assets/nao_existe_12345.png"
theme:
  primary_color: "#123456"
llm:
  providers:
    - name: "openrouter"
      model: "test-model"
system_prompt:
  role: "Professor de teste"
  tone: "Didático"
"""
    missing_logo_file.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(missing_logo_file))
    assert "logotipo configurado não foi encontrado" in str(exc.value)


def test_system_prompt_builder():
    """Testa se a montagem do prompt de sistema inclui diretrizes e restrições."""
    config = load_config("config.yaml")
    prompt = config.system_prompt.build_full_system_prompt()
    assert "IDENTIDADE E PAPEL:" in prompt
    assert "TOM DE VOZ:" in prompt
    assert config.system_prompt.role in prompt


def test_rag_config_in_default_config():
    """Testa se o bloco rag carregado no config.yaml padrão está correto."""
    config = load_config("config.yaml")
    assert config.rag is not None
    assert config.rag.enabled is True
    assert 200 <= config.rag.chunk_size <= 2000
    assert 0 <= config.rag.chunk_overlap <= (config.rag.chunk_size // 2)
    assert 1 <= config.rag.top_k <= 10
    assert 0.0 <= config.rag.vector_weight <= 1.0
    assert 0.0 <= config.rag.text_weight <= 1.0
    assert config.rag.min_relevance_score >= 0.0
    assert 0.50 <= config.rag.hit_rate_threshold <= 1.00


def test_rag_config_overlap_too_large(tmp_path):
    """Testa se erro é lançado quando chunk_overlap > chunk_size // 2."""
    bad_rag_file = tmp_path / "bad_rag.yaml"
    content = """
app:
  title: "Teste"
  description: "Desc"
llm:
  providers:
    - name: "openrouter"
      model: "test-model"
system_prompt:
  role: "Professor"
  tone: "Didático"
rag:
  enabled: true
  chunk_size: 400
  chunk_overlap: 250  # Inválido: > 200 (metade de 400)
"""
    bad_rag_file.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigValidationError) as exc:
        load_config(str(bad_rag_file))
    assert "não pode ser maior que a metade de chunk_size" in str(exc.value)

