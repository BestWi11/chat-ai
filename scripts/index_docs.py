#!/usr/bin/env python3
"""
Script de Indexação de Documentos Markdown para o Supabase (RAG).
Lê arquivos .md em documentos/, fatia em seções/chunks com overlap,
gera embeddings locais (384 dimensões) e grava na tabela document_chunks sob um version_id.
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from postgrest import SyncPostgrestClient

# Garante acesso aos módulos em src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Carrega variáveis do .env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.rag.chunker import load_and_chunk_documents, DocumentChunk
from src.rag.embedder import get_embedder


def get_git_version() -> str:
    """Tenta obter o hash curto do commit Git atual, ou gera um timestamp como fallback."""
    try:
        git_hash = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
        if git_hash:
            return f"v_{git_hash}"
    except Exception:
        pass
    return f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def normalize_supabase_url(url: str) -> str:
    """Normaliza a URL base para o endpoint REST do PostgREST."""
    clean = url.strip().rstrip("/")
    if not clean.endswith("/rest/v1"):
        return f"{clean}/rest/v1"
    return clean


def get_supabase_client(
    supabase_url: Optional[str] = None,
    service_role_key: Optional[str] = None
) -> Optional[SyncPostgrestClient]:
    """Cria e retorna o cliente PostgREST autenticado com service_role_key."""
    url = (os.getenv("SUPABASE_URL", "") if supabase_url is None else supabase_url).strip()
    
    if service_role_key is None:
        key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or
            os.getenv("SUPABASE_KEY", "") or
            os.getenv("SUPABASE_ANON_KEY", "")
        ).strip()
    else:
        key = service_role_key.strip()

    if not url or not key:
        return None

    rest_url = normalize_supabase_url(url)
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    return SyncPostgrestClient(rest_url, headers=headers)


def index_documents(
    docs_dir: str = "documentos",
    version_id: Optional[str] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    batch_size: int = 50,
    clean_existing: bool = True,
    client: Optional[SyncPostgrestClient] = None
) -> Dict[str, Any]:
    """
    Executa o pipeline completo de leitura, fatiamento, embedding e upload no Supabase.
    Retorna métricas da execução.
    """
    start_time = datetime.now()
    resolved_version = version_id or get_git_version()
    full_docs_dir = os.path.abspath(docs_dir) if os.path.isabs(docs_dir) else os.path.join(PROJECT_ROOT, docs_dir)

    print(f"🚀 Iniciando indexação RAG")
    print(f"📂 Diretório de documentos: {full_docs_dir}")
    print(f"🏷️  Versão do índice: {resolved_version}")
    print(f"✂️  Chunk size: {chunk_size} | Overlap: {chunk_overlap}")

    if not os.path.exists(full_docs_dir):
        raise FileNotFoundError(f"Diretório não encontrado: {full_docs_dir}")

    # 1. Carrega e fatia os arquivos Markdown
    chunks: List[DocumentChunk] = load_and_chunk_documents(
        directory_path=full_docs_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    if not chunks:
        raise ValueError(f"Nenhum trecho gerado. Verifique se há arquivos .md não vazios em {full_docs_dir}")

    # Agrupa por documentos para exibição de métricas
    docs_processed = sorted(list(set(c.document_name for c in chunks)))
    print(f"📄 Documentos encontrados ({len(docs_processed)}): {', '.join(docs_processed)}")
    print(f"🧩 Total de chunks gerados: {len(chunks)}")

    # 2. Conexão com o Supabase
    pg_client = client or get_supabase_client()
    if pg_client is None:
        raise RuntimeError(
            "Credenciais do Supabase não encontradas. "
            "Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no seu arquivo .env ou como variáveis de ambiente."
        )

    # 3. Limpeza prévia de registros da mesma versão (idempotência)
    if clean_existing:
        try:
            print(f"🧹 Verificando se já existem chunks com a versão '{resolved_version}'...")
            pg_client.from_("document_chunks").delete().eq("version_id", resolved_version).execute()
        except Exception as e:
            print(f"ℹ️  Nenhum chunk anterior para limpar ou aviso: {e}")

    # 4. Geração de Embeddings em lote
    print("🧠 Gerando embeddings com modelo local (paraphrase-multilingual-MiniLM-L12-v2)...")
    embedder = get_embedder()
    texts = [c.content for c in chunks]
    embeddings = embedder.embed_batch(texts, batch_size=32)

    # 5. Inserção em lotes no Supabase
    print(f"💾 Enviando chunks para a tabela 'document_chunks' no Supabase em lotes de {batch_size}...")
    total_inserted = 0

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i : i + batch_size]
        batch_embeddings = embeddings[i : i + batch_size]

        records: List[Dict[str, Any]] = []
        for chunk, emb in zip(batch_chunks, batch_embeddings):
            records.append({
                "document_name": chunk.document_name,
                "section_title": chunk.section_title,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "embedding": emb,
                "version_id": resolved_version
            })

        response = pg_client.from_("document_chunks").insert(records).execute()
        inserted_count = len(response.data) if response.data else len(records)
        total_inserted += inserted_count
        print(f"   ↳ Inseridos {total_inserted}/{len(chunks)} chunks...")

    elapsed_seconds = (datetime.now() - start_time).total_seconds()
    print(f"✅ Indexação concluída com sucesso em {elapsed_seconds:.2f}s!")
    print(f"   • Versão indexada: {resolved_version}")
    print(f"   • Documentos processados: {len(docs_processed)}")
    print(f"   • Total de chunks no banco: {total_inserted}")

    return {
        "status": "success",
        "version_id": resolved_version,
        "docs_count": len(docs_processed),
        "chunks_count": total_inserted,
        "elapsed_seconds": elapsed_seconds
    }


def main():
    default_chunk_size = 1200
    default_overlap = 100
    try:
        from src.config_loader import load_config
        cfg = load_config()
        if hasattr(cfg, "rag") and cfg.rag:
            default_chunk_size = cfg.rag.chunk_size
            default_overlap = cfg.rag.chunk_overlap
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Indexador de documentos Markdown para Supabase pgvector.")
    parser.add_argument("--docs-dir", default="documentos", help="Diretório dos arquivos .md (default: documentos)")
    parser.add_argument("--version", default=None, help="ID da versão do índice (default: commit git ou timestamp)")
    parser.add_argument("--chunk-size", type=int, default=default_chunk_size, help=f"Tamanho máximo de cada chunk (default: {default_chunk_size})")
    parser.add_argument("--chunk-overlap", type=int, default=default_overlap, help=f"Sobreposição entre chunks (default: {default_overlap})")
    parser.add_argument("--batch-size", type=int, default=50, help="Tamanho do lote de inserção no banco (default: 50)")
    parser.add_argument("--no-clean", action="store_true", help="Não apagar chunks anteriores com a mesma versão")

    args = parser.parse_args()

    try:
        index_documents(
            docs_dir=args.docs_dir,
            version_id=args.version,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            batch_size=args.batch_size,
            clean_existing=not args.no_clean
        )
    except Exception as e:
        print(f"\n❌ Erro durante a indexação: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
