"""
Módulo de Recuperação Híbrida no Supabase (Retriever).
Executa busca combinada de texto pleno e vetores com RRF através da função RPC no Postgres.
"""

import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

from src.rag.embedder import get_embedder


class SearchResult(BaseModel):
    """Representação de um trecho retornado pela busca híbrida."""
    id: int
    document_name: str = Field(..., description="Nome do documento fonte")
    section_title: str = Field(..., description="Título da seção")
    content: str = Field(..., description="Conteúdo textual do trecho")
    final_score: float = Field(..., description="Pontuação final calculada pelo algoritmo RRF")


def normalize_supabase_url(url: str) -> str:
    """Sanitiza e normaliza a URL do Supabase para o formato base."""
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith("/rest/v1"):
        cleaned = cleaned[:-len("/rest/v1")].rstrip("/")
    return cleaned


class SupabaseRetriever:
    """Cliente de consulta e busca híbrida no banco de dados Supabase."""

    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        if supabase_url is not None:
            raw_url = supabase_url
        else:
            raw_url = os.getenv("SUPABASE_URL", "")

        if supabase_key is not None:
            self.key = supabase_key.strip()
        else:
            self.key = (os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")).strip()

        self.url = normalize_supabase_url(raw_url)

        self._client = None
        if self.url and self.key:
            try:
                from postgrest import SyncPostgrestClient
                rest_url = f"{self.url}/rest/v1"
                headers = {
                    "apikey": self.key,
                    "Authorization": f"Bearer {self.key}"
                }
                self._client = SyncPostgrestClient(rest_url, headers=headers)
            except Exception as e:
                print(f"⚠️ Aviso: Não foi possível instanciar o cliente Postgrest: {e}")

    def is_configured(self) -> bool:
        """Verifica se o cliente Supabase possui URL e chave configuradas."""
        return bool(self._client and self.url and self.key)

    def get_active_version(self) -> str:
        """Consulta a versão ativa do índice na tabela rag_metadata."""
        if not self.is_configured():
            return "v1"

        try:
            res = self._client.from_("rag_metadata").select("active_version").eq("id", 1).execute()
            if res.data and len(res.data) > 0:
                return str(res.data[0].get("active_version", "v1"))
        except Exception as e:
            print(f"⚠️ Aviso ao buscar active_version no Supabase: {e}")

        return "v1"

    def search(
        self,
        query: str,
        top_k: int = 3,
        vector_weight: float = 0.6,
        text_weight: float = 0.4,
        min_score: float = 0.005,
        version: Optional[str] = None,
        match_count: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Executa a busca híbrida (semântica + texto pleno) com fusão RRF no Supabase.
        Retorna trechos relevantes que atingiram a pontuação mínima configurada.
        """
        if match_count is not None:
            top_k = match_count

        cleaned_query = query.strip()
        if not cleaned_query or not self.is_configured():
            return []

        target_version = version or self.get_active_version()

        try:
            # 1. Gera o vetor de embedding localmente (384 dimensões)
            embedder = get_embedder()
            query_embedding = embedder.embed_text(cleaned_query)

            # 2. Chama a função RPC de busca híbrida no banco
            rpc_params = {
                "query_text": cleaned_query,
                "query_embedding": query_embedding,
                "target_version": target_version,
                "match_count": top_k,
                "vector_weight": float(vector_weight),
                "text_weight": float(text_weight)
            }

            response = self._client.rpc("hybrid_search_chunks", rpc_params).execute()
            raw_matches = response.data or []

            results: List[SearchResult] = []
            for row in raw_matches:
                score = float(row.get("final_score", 0.0))
                if score >= min_score:
                    results.append(
                        SearchResult(
                            id=int(row.get("id")),
                            document_name=str(row.get("document_name", "")),
                            section_title=str(row.get("section_title", "")),
                            content=str(row.get("content", "")),
                            final_score=score
                        )
                    )

            return results

        except Exception as e:
            print(f"⚠️ Erro ao executar busca híbrida no Supabase: {e}")
            return []
