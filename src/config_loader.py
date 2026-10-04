"""Módulo de validação e carregamento do arquivo de configuração (config.yaml)."""

import os
import re
import yaml
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


HEX_COLOR_REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


class ConfigValidationError(Exception):
    """Exceção customizada com mensagens amigáveis em Português."""
    pass


class AppConfig(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Título do assistente")
    description: str = Field(..., min_length=1, max_length=300, description="Descrição do assistente")
    logo_path: Optional[str] = Field(default="", description="Caminho do arquivo de logo")
    logo_width: int = Field(default=80, ge=20, le=400, description="Largura do logo em pixels")

    @field_validator("logo_path")
    @classmethod
    def validate_logo_path(cls, v: Optional[str]) -> str:
        if v and v.strip():
            cleaned = v.strip()
            if not os.path.exists(cleaned):
                raise ValueError(f"O arquivo de logotipo configurado não foi encontrado no caminho: '{cleaned}'.")
            return cleaned
        return ""


class ThemeConfig(BaseModel):
    primary_color: str = Field(default="#1E3A8A", description="Cor primária (#RRGGBB)")
    secondary_color: str = Field(default="#3B82F6", description="Cor secundária (#RRGGBB)")
    background_color: str = Field(default="#0F172A", description="Cor de fundo (#RRGGBB)")
    text_color: str = Field(default="#F8FAFC", description="Cor do texto (#RRGGBB)")

    @field_validator("primary_color", "secondary_color", "background_color", "text_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not v or not HEX_COLOR_REGEX.match(v.strip()):
            raise ValueError(f"A cor '{v}' não é um código hexadecimal válido (exemplo válido: '#1E3A8A' ou '#3B82F6').")
        return v.strip().upper()


class LLMProviderConfig(BaseModel):
    name: str = Field(..., description="Nome do provedor ('openrouter', 'openai', 'anthropic')")
    model: str = Field(..., min_length=1, description="Identificador do modelo")
    max_tokens: int = Field(default=1024, ge=64, le=8192, description="Limite máximo de tokens")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperatura de amostragem")

    @field_validator("name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        valid_names = {"openrouter", "openai", "anthropic"}
        cleaned = v.strip().lower()
        if cleaned not in valid_names:
            raise ValueError(f"Provedor '{v}' inválido. Valores aceitos: {', '.join(sorted(valid_names))}.")
        return cleaned


class LLMConfig(BaseModel):
    timeout_seconds: int = Field(default=30, ge=5, le=120, description="Timeout por requisição em segundos")
    providers: List[LLMProviderConfig] = Field(..., min_length=1, description="Lista ordenada de provedores")


class SystemPromptConfig(BaseModel):
    role: str = Field(..., min_length=5, description="Papel pedagógico do assistente")
    tone: str = Field(..., min_length=3, description="Tom e estilo da resposta")
    restrictions: List[str] = Field(default_factory=list, description="Lista de restrições de conduta")
    custom_instructions: str = Field(default="", description="Instruções adicionais")

    def build_full_system_prompt(self) -> str:
        """Monta o prompt de sistema estruturado."""
        lines = [
            f"IDENTIDADE E PAPEL: {self.role}",
            f"TOM DE VOZ: {self.tone}"
        ]
        if self.restrictions:
            lines.append("RESTRIÇÕES E DIRETRIZES DE SEGURANÇA:")
            for r in self.restrictions:
                lines.append(f"- {r}")
        if self.custom_instructions:
            lines.append(f"INSTRUÇÕES ADICIONAIS:\n{self.custom_instructions}")
        return "\n\n".join(lines)


class AssistantConfig(BaseModel):
    app: AppConfig
    theme: ThemeConfig = Field(default_factory=ThemeConfig)
    llm: LLMConfig
    system_prompt: SystemPromptConfig
    example_questions: List[str] = Field(default_factory=list, max_length=10)


def load_config(config_path: str = "config.yaml") -> AssistantConfig:
    """
    Carrega e valida o arquivo config.yaml.
    Gera mensagens explicativas em caso de erro.
    """
    if not os.path.exists(config_path):
        raise ConfigValidationError(
            f"Arquivo de configuração '{config_path}' não foi encontrado na raiz do projeto."
        )

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigValidationError(
            f"Erro de sintaxe no arquivo YAML '{config_path}':\n{exc}"
        ) from exc

    if not isinstance(raw_data, dict):
        raise ConfigValidationError(
            f"O arquivo '{config_path}' deve conter um mapeamento YAML (dicionário de chave/valor)."
        )

    try:
        config = AssistantConfig.model_validate(raw_data)
        return config
    except Exception as exc:
        raise ConfigValidationError(
            f"Falha na validação das configurações em '{config_path}':\n{exc}"
        ) from exc
