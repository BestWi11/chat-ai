"""Módulo cliente de integração com LLMs com suporte a streaming e fallback de múltiplos provedores."""

import os
import time
from typing import List, Dict, Generator, Optional
from dotenv import load_dotenv

# Carrega variáveis de ambiente de .env para desenvolvimento local
load_dotenv()

from src.config_loader import AssistantConfig, LLMProviderConfig


class LLMClient:
    """Cliente para orquestração de chamadas de LLM com fallback automático."""

    def __init__(self, config: AssistantConfig):
        self.config = config

    def _get_api_key(self, provider_name: str) -> Optional[str]:
        """Obtém a chave de API correspondente ao provedor a partir das variáveis de ambiente."""
        env_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        env_var = env_map.get(provider_name, f"{provider_name.upper()}_API_KEY")
        key = os.getenv(env_var, "").strip()
        return key if key else None

    def _stream_openrouter_or_openai(
        self,
        provider: LLMProviderConfig,
        messages: List[Dict[str, str]],
        api_key: str
    ) -> Generator[str, None, None]:
        """Realiza streaming via SDK compatível com OpenAI (OpenRouter ou OpenAI nativo)."""
        from openai import OpenAI

        if provider.name == "openrouter":
            # Cabeçalhos HTTP exigem caracteres ASCII puros
            safe_title = self.config.app.title.encode("ascii", "ignore").decode("ascii") or "Chat-AI"
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://huggingface.co/spaces/BestWill/chat-ai-personalizado",
                    "X-Title": safe_title
                }
            )
        else:
            client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=provider.model,
            messages=messages,
            max_tokens=provider.max_tokens,
            temperature=provider.temperature,
            stream=True,
            timeout=self.config.llm.timeout_seconds
        )

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

    def _stream_anthropic(
        self,
        provider: LLMProviderConfig,
        messages: List[Dict[str, str]],
        system_prompt: str,
        api_key: str
    ) -> Generator[str, None, None]:
        """Realiza streaming via SDK da Anthropic."""
        import anthropic

        client = anthropic.Anthropic(api_key=api_key, timeout=self.config.llm.timeout_seconds)

        # Filtra mensagens (Anthropic exige que system prompt seja passado separadamente)
        chat_messages = [m for m in messages if m["role"] != "system"]

        with client.messages.stream(
            model=provider.model,
            system=system_prompt,
            messages=chat_messages,
            max_tokens=provider.max_tokens,
            temperature=provider.temperature
        ) as stream:
            for text in stream.text_stream:
                yield text

    def stream_chat(
        self,
        history: List[Dict[str, str]]
    ) -> Generator[str, None, None]:
        """
        Gera resposta em streaming tentando os provedores na ordem de preferência configurada.
        Se o provedor atual falhar, tenta o próximo silenciosamente.
        Se todos falharem, exibe diagnóstico didático.
        """
        system_prompt_text = self.config.system_prompt.build_full_system_prompt()
        
        # Constrói a lista completa de mensagens para modelos estilo OpenAI
        full_messages = [{"role": "system", "content": system_prompt_text}]
        for msg in history:
            full_messages.append({"role": msg["role"], "content": msg["content"]})

        failed_attempts = []

        for provider in self.config.llm.providers:
            api_key = self._get_api_key(provider.name)
            if not api_key:
                failed_attempts.append(
                    f"**{provider.name.capitalize()}** (`{provider.model}`): Chave `{provider.name.upper()}_API_KEY` não configurada no ambiente."
                )
                continue

            try:
                if provider.name in ("openrouter", "openai"):
                    generator = self._stream_openrouter_or_openai(provider, full_messages, api_key)
                elif provider.name == "anthropic":
                    generator = self._stream_anthropic(provider, full_messages, system_prompt_text, api_key)
                else:
                    failed_attempts.append(f"**{provider.name}**: Provedor não suportado.")
                    continue

                # Itera sobre o streaming. Se falhar durante a chamada, cai no except.
                has_yielded = False
                for text_chunk in generator:
                    has_yielded = True
                    yield text_chunk

                # Se concluiu a geração com sucesso, encerra a função
                if has_yielded:
                    return

            except Exception as e:
                error_msg = str(e)
                # Resumo limpo do erro para evitar expor URLs de autenticação completas
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    reason = "Limite de requisições excedido ou modelo sobrecarregado (429)."
                elif "401" in error_msg or "auth" in error_msg.lower():
                    reason = "Chave de API inválida ou expirada (401)."
                elif "timeout" in error_msg.lower():
                    reason = f"Tempo de espera esgotado ({self.config.llm.timeout_seconds}s)."
                else:
                    reason = f"Erro: {error_msg[:120]}"

                failed_attempts.append(
                    f"**{provider.name.capitalize()}** (`{provider.model}`): {reason}"
                )
                continue

        # Se nenhum provedor conseguiu responder:
        diagnostico = (
            "⚠️ **Não foi possível obter resposta no momento.**\n\n"
            "Todos os provedores configurados foram consultados e apresentaram as seguintes ocorrências:\n\n"
        )
        for attempt in failed_attempts:
            diagnostico += f"- {attempt}\n"

        diagnostico += (
            "\n💡 **Como resolver:**\n"
            "1. Verifique se a variável `OPENROUTER_API_KEY` foi adicionada nas **Settings > Variables and secrets** do Hugging Face Spaces (ou no seu `.env` local).\n"
            "2. Se estiver usando o modelo gratuito do OpenRouter, ele pode estar temporariamente congestionado. Tente novamente em alguns instantes ou adicione outro modelo no `config.yaml`."
        )
        yield diagnostico
