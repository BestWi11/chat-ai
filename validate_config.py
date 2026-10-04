#!/usr/bin/env python3
"""
Portão de Qualidade e Validação de Configuração (Quality Gate).
Executado localmente e no pipeline de CI/CD do GitHub Actions.
"""

import os
import sys
import re
from src.config_loader import load_config, ConfigValidationError

SECRET_PATTERNS = [
    (re.compile(r"sk-or-[a-zA-Z0-9_-]{20,}"), "Chave do OpenRouter (sk-or-...)"),
    (re.compile(r"sk-ant-[a-zA-Z0-9_-]{20,}"), "Chave da Anthropic (sk-ant-...)"),
    (re.compile(r"sk-(?!or-|ant-)[a-zA-Z0-9_-]{20,}"), "Chave da OpenAI (sk-...)"),
    (re.compile(r"hf_[a-zA-Z0-9_-]{30,}"), "Token do Hugging Face (hf_...)"),
]

IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
IGNORED_FILES = {".env", ".env.example"}


def check_for_secret_leaks(root_dir: str = ".") -> list[str]:
    """Escaneia os arquivos do repositório procurando por chaves de API commitadas por engano."""
    findings = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file in IGNORED_FILES or file.endswith((".png", ".jpg", ".jpeg", ".ico", ".pyc")):
                continue
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, start=1):
                        for pattern, name in SECRET_PATTERNS:
                            if pattern.search(line):
                                findings.append(
                                    f"Arquivo '{file_path}' (linha {line_idx}): Possível vazamento de {name}."
                                )
            except Exception as e:
                # Ignora arquivos binários ou ilegíveis
                pass
    return findings


def run_quality_gate(config_path: str = "config.yaml") -> bool:
    print("=" * 60)
    print("🛡️  INICIANDO PORTÃO DE TESTES E QUALIDADE (CI/CD)")
    print("=" * 60)

    has_error = False

    # 1. Teste de Configuração (T1 a T4)
    print("\n🔍 [1/2] Validando sintaxe e regras do 'config.yaml'...")
    try:
        config = load_config(config_path)
        print(f"  ✅ [T1] Sintaxe YAML válida.")
        print(f"  ✅ [T2] Schema e campos validados com sucesso.")
        print(f"  ✅ [T3] Cores hexadecimais válidas (Primária: {config.theme.primary_color}).")
        if config.app.logo_path:
            print(f"  ✅ [T4] Arquivo de logo encontrado: '{config.app.logo_path}'.")
        else:
            print(f"  ℹ️  [T4] Nenhum logo configurado (opcional).")
        print(f"  🤖 Provedor principal: {config.llm.providers[0].name} ({config.llm.providers[0].model})")
    except ConfigValidationError as err:
        print(f"\n❌ ERRO NA CONFIGURAÇÃO:")
        print(f"{err}")
        has_error = True

    # 2. Teste de Vazamento de Segredos (T5)
    print("\n🔐 [2/2] Verificando segurança contra vazamento de chaves de API...")
    leaks = check_for_secret_leaks(".")
    if leaks:
        print("\n❌ ALERTA CRÍTICO DE SEGURANÇA: Chaves de API detectadas nos arquivos:")
        for leak in leaks:
            print(f"  🚨 {leak}")
        print("\n👉 NUNCA coloque chaves de API no código ou no config.yaml!")
        print("👉 Use as configurações do Hugging Face Spaces (Settings > Variables and secrets).")
        has_error = True
    else:
        print("  ✅ [T5] Nenhuma chave de API detectada no código do repositório.")

    print("\n" + "=" * 60)
    if has_error:
        print("❌ PORTÃO DE QUALIDADE REPROVADO! O deploy será bloqueado.")
        print("=" * 60)
        return False
    else:
        print("🎉 PORTÃO DE QUALIDADE APROVADO COM SUCESSO!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = run_quality_gate()
    sys.exit(0 if success else 1)
