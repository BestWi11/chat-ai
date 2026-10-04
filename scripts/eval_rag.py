#!/usr/bin/env python3
"""
Script de Avaliação Automatizada de Qualidade RAG (Eval Gate).
Executa bateria de perguntas de teste contra o índice no Supabase,
calcula Hit Rate@K e MRR, e promove a versão ativa em caso de aprovação.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from postgrest import SyncPostgrestClient

# Garante acesso aos módulos em src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from src.rag.retriever import SupabaseRetriever
from scripts.index_docs import get_supabase_client


def normalize_title(text: str) -> str:
    """Normaliza strings removendo pontuações e espaçamentos extras para comparação flexível."""
    return "".join(c.lower() for c in text if c.isalnum())


def is_matching_chunk(result_doc: str, result_section: str, expected_doc: str, expected_section: str) -> bool:
    """
    Verifica se um trecho retornado pela busca corresponde ao documento e seção esperados.
    """
    doc_match = expected_doc.strip().lower() in result_doc.strip().lower()
    
    # Compara seções com tolerância a subtítulos ou variações menores
    norm_result_sec = normalize_title(result_section)
    norm_exp_sec = normalize_title(expected_section)
    section_match = norm_exp_sec in norm_result_sec or norm_result_sec in norm_exp_sec

    return doc_match and section_match


def calculate_metrics(
    eval_results: List[Dict[str, Any]],
    top_k: int = 3
) -> Tuple[float, float]:
    """
    Calcula Hit Rate@K e MRR a partir da lista de avaliações individuais.
    """
    if not eval_results:
        return 0.0, 0.0

    total = len(eval_results)
    hits = sum(1 for r in eval_results if r["hit"])
    mrr = sum(r["reciprocal_rank"] for r in eval_results) / total
    hit_rate = hits / total

    return hit_rate, mrr


def promote_active_version(version_id: str, client: Optional[SyncPostgrestClient] = None) -> bool:
    """
    Promove a versão aprovada no Supabase atualizando a tabela rag_metadata (id=1).
    Requer SUPABASE_SERVICE_ROLE_KEY para gravação via RLS.
    """
    pg_client = client or get_supabase_client()
    if pg_client is None:
        print("⚠️ Não foi possível promover a versão: credenciais com permissão de escrita não encontradas.")
        return False

    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        res = pg_client.from_("rag_metadata").update({
            "active_version": version_id,
            "updated_at": now_iso
        }).eq("id", 1).execute()

        print(f"🎉 Versão '{version_id}' promovida a 'active_version' com sucesso no Supabase!")
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar rag_metadata no Supabase: {e}")
        return False


def run_evaluation(
    questions_file: str = "tests/eval_questions.json",
    version_id: Optional[str] = None,
    top_k: int = 3,
    threshold: float = 0.80,
    promote: bool = False,
    retriever: Optional[SupabaseRetriever] = None,
    client: Optional[SyncPostgrestClient] = None
) -> Dict[str, Any]:
    """
    Executa a bateria de testes e retorna relatório com métricas calculadas.
    """
    questions_path = os.path.abspath(questions_file) if os.path.isabs(questions_file) else os.path.join(PROJECT_ROOT, questions_file)
    if not os.path.exists(questions_path):
        raise FileNotFoundError(f"Arquivo de perguntas não encontrado: {questions_path}")

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError(f"O arquivo {questions_path} deve conter uma lista JSON não-vazia de perguntas.")

    rag_retriever = retriever or SupabaseRetriever()
    target_version = version_id or rag_retriever.get_active_version()

    print(f"\n========================================================")
    print(f"🎯 INICIANDO AVALIAÇÃO RAG (Quality Gate T14 / T15)")
    print(f"📋 Perguntas de teste: {len(questions)} itens")
    print(f"🏷️  Versão alvo: {target_version}")
    print(f"🔍 Top-K avaliado: {top_k} | Limiar de aprovação: {threshold * 100:.1f}%")
    print(f"========================================================\n")

    eval_items: List[Dict[str, Any]] = []

    for idx, item in enumerate(questions, 1):
        q_id = item.get("id", f"q-{idx}")
        question_text = item["question"]
        expected_doc = item["expected_document"]
        expected_sec = item["expected_section"]

        search_results = rag_retriever.search(
            query=question_text,
            top_k=top_k,
            version=target_version,
            min_score=0.005
        )

        hit = False
        hit_rank = 0
        reciprocal_rank = 0.0

        for rank, match in enumerate(search_results, 1):
            if is_matching_chunk(
                result_doc=match.document_name,
                result_section=match.section_title,
                expected_doc=expected_doc,
                expected_section=expected_sec
            ):
                hit = True
                hit_rank = rank
                reciprocal_rank = 1.0 / rank
                break

        eval_items.append({
            "id": q_id,
            "question": question_text,
            "expected_doc": expected_doc,
            "expected_sec": expected_sec,
            "hit": hit,
            "rank": hit_rank,
            "reciprocal_rank": reciprocal_rank,
            "matches": [f"{r.document_name} ({r.section_title})" for r in search_results]
        })

        status_emoji = "✅" if hit else "❌"
        rank_str = f"Rank {hit_rank}" if hit else "Não encontrado"
        print(f"[{status_emoji}] {q_id}: \"{question_text[:50]}...\" -> {rank_str}")

    hit_rate, mrr = calculate_metrics(eval_items, top_k=top_k)
    passed = hit_rate >= threshold

    print(f"\n--------------------------------------------------------")
    print(f"📊 RESULTADO FINAL DA AVALIAÇÃO:")
    print(f"   • Hit Rate@{top_k}: {hit_rate * 100:.1f}% (Mínimo exigido: {threshold * 100:.1f}%)")
    print(f"   • MRR (Mean Reciprocal Rank): {mrr:.4f}")
    print(f"   • Status: {'APROVADO ✅' if passed else 'REPROVADO ❌'}")
    print(f"--------------------------------------------------------\n")

    if not passed:
        print("⚠️ Portão de testes REPROVADO. A nova versão do índice não atende ao limiar de qualidade.")
        return {
            "passed": False,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "promoted": False,
            "details": eval_items
        }

    promoted = False
    if promote:
        promoted = promote_active_version(target_version, client=client)

    return {
        "passed": True,
        "hit_rate": hit_rate,
        "mrr": mrr,
        "promoted": promoted,
        "details": eval_items
    }


def main():
    parser = argparse.ArgumentParser(description="Portão de Avaliação Automatizada de Qualidade RAG (Hit Rate@3 e MRR).")
    parser.add_argument("--questions", default="tests/eval_questions.json", help="Caminho do arquivo de perguntas (JSON)")
    parser.add_argument("--version", default=None, help="Versão do índice a avaliar (default: active_version no Supabase)")
    parser.add_argument("--top-k", type=int, default=3, help="Top-K trechos considerados (default: 3)")
    parser.add_argument("--threshold", type=float, default=0.80, help="Limiar mínimo de Hit Rate para aprovação (default: 0.80)")
    parser.add_argument("--promote", action="store_true", help="Promover versão para active_version no Supabase se aprovado")

    args = parser.parse_args()

    try:
        report = run_evaluation(
            questions_file=args.questions,
            version_id=args.version,
            top_k=args.top_k,
            threshold=args.threshold,
            promote=args.promote
        )

        if not report["passed"]:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Erro durante a avaliação RAG: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
