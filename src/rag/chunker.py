"""
Módulo de Fatiamento (Chunking) de Documentos Markdown.
Preserva cabeçalhos de seção e divide o conteúdo respeitando limites de caracteres e sobreposição.
"""

import os
import re
from typing import List, Tuple
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Representação de um trecho de documento fatiado."""
    document_name: str = Field(..., description="Nome do arquivo de origem (ex: parte-01.md)")
    section_title: str = Field(..., description="Título da seção ou subtítulo Markdown")
    chunk_index: int = Field(..., description="Índice sequencial do chunk no documento")
    content: str = Field(..., description="Texto do trecho")


def split_markdown_by_headings(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Divide o texto Markdown por cabeçalhos (#, ##, ###).
    Retorna uma lista de tuplas: (titulo_da_secao, conteudo_da_secao).
    """
    lines = markdown_text.splitlines()
    sections: List[Tuple[str, str]] = []
    
    current_title = "Geral"
    current_lines: List[str] = []
    
    heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$")

    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            # Se já tínhamos conteúdo acumulado, fecha a seção anterior
            section_body = "\n".join(current_lines).strip()
            if section_body:
                sections.append((current_title, section_body))
            current_title = match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    # Adiciona a última seção
    final_body = "\n".join(current_lines).strip()
    if final_body:
        sections.append((current_title, final_body))

    return sections if sections else [("Geral", markdown_text.strip())]


def slice_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Divide um bloco de texto em fatias de até chunk_size caracteres com overlap,
    tentando quebrar em limites naturais (parágrafos, pontuação ou espaços).
    """
    cleaned = text.strip()
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: List[str] = []
    start = 0
    text_len = len(cleaned)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # Se não chegamos ao final, tenta encontrar uma quebra limpa
        if end < text_len:
            # Procura por quebra de parágrafo, ponto final ou espaço próximo ao final
            slice_segment = cleaned[start:end]
            cut_point = -1
            for separator in ["\n\n", ".\n", ". ", "; ", "\n", " "]:
                pos = slice_segment.rfind(separator)
                if pos != -1 and pos > chunk_size * 0.5:
                    cut_point = start + pos + len(separator)
                    break
            
            if cut_point != -1:
                end = cut_point

        chunk_str = cleaned[start:end].strip()
        if chunk_str:
            chunks.append(chunk_str)

        if end >= text_len:
            break

        # Próximo início considerando o overlap
        start = max(end - chunk_overlap, start + 1)

    return chunks


def chunk_markdown(content: str, document_name: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[DocumentChunk]:
    """
    Fatia o conteúdo completo de um arquivo Markdown gerando uma lista de DocumentChunk.
    """
    sections = split_markdown_by_headings(content)
    all_chunks: List[DocumentChunk] = []
    chunk_counter = 0

    for section_title, section_body in sections:
        text_slices = slice_text_into_chunks(section_body, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for t_slice in text_slices:
            all_chunks.append(
                DocumentChunk(
                    document_name=document_name,
                    section_title=section_title,
                    chunk_index=chunk_counter,
                    content=t_slice
                )
            )
            chunk_counter += 1

    return all_chunks


def load_and_chunk_documents(
    directory_path: str = "documentos",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[DocumentChunk]:
    """
    Lê todos os arquivos .md da pasta de documentos e retorna os chunks estruturados.
    """
    if not os.path.exists(directory_path):
        return []

    collected_chunks: List[DocumentChunk] = []

    # Lista e ordena os arquivos para garantir consistência
    files = sorted([f for f in os.listdir(directory_path) if f.endswith(".md")])
    for filename in files:
        full_path = os.path.join(directory_path, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            doc_chunks = chunk_markdown(
                content=content,
                document_name=filename,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            collected_chunks.extend(doc_chunks)
        except Exception as e:
            print(f"⚠️ Aviso: Falha ao ler documento '{filename}': {e}")

    return collected_chunks
