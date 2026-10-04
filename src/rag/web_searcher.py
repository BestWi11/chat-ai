"""
Módulo de Busca na Web para Fallback de Conhecimento Externo.
Permite ao assistente consultar fontes confiáveis na internet quando a dúvida
não constar nas apostilas do curso.
"""

from typing import List, Dict, Any

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None


def search_web(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """
    Realiza busca na web utilizando ddgs/duckduckgo_search sem requisição de API paga.
    Retorna uma lista com título, link e trecho (body) das páginas encontradas.
    """
    cleaned = query.strip()
    if not cleaned or DDGS is None:
        return []

    try:
        results: List[Dict[str, str]] = []
        with DDGS() as ddgs:
            raw_results = ddgs.text(cleaned, max_results=max_results)
            for item in raw_results:
                title = str(item.get("title", "")).strip()
                href = str(item.get("href", "")).strip()
                body = str(item.get("body", "")).strip()
                if title and href:
                    results.append({
                        "title": title,
                        "href": href,
                        "body": body
                    })

        return results

    except Exception as e:
        print(f"⚠️ Aviso na busca web externa: {e}")
        return []
