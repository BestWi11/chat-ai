-- ==============================================================================
-- Script de Configuração Inicial do Banco de Dados no Supabase (Parte 2: RAG)
-- Execute este script no SQL Editor do painel do seu projeto no Supabase
-- ==============================================================================

-- 1. Habilitar a extensão pgvector para suporte a vetores e busca semântica
create extension if not exists vector;

-- 2. Tabela de Metadados do Índice (Controla qual versão o assistente consulta)
create table if not exists rag_metadata (
    id int primary key default 1,
    active_version text not null,
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Insere o registro inicial de versão se ainda não existir
insert into rag_metadata (id, active_version) 
values (1, 'v1')
on conflict (id) do nothing;

-- 3. Tabela de Trechos de Documentos (Chunks)
create table if not exists document_chunks (
    id bigserial primary key,
    version_id text not null,
    document_name text not null,
    section_title text not null,
    chunk_index int not null,
    content text not null,
    embedding vector(384) not null,
    fts_tokens tsvector generated always as (to_tsvector('portuguese', content)) stored,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- 4. Criação de Índices para Alto Desempenho
create index if not exists idx_chunks_version on document_chunks (version_id);
create index if not exists idx_chunks_fts on document_chunks using gin (fts_tokens);
create index if not exists idx_chunks_embedding on document_chunks using hnsw (embedding vector_cosine_ops);

-- 5. Função RPC para Busca Híbrida com Reciprocal Rank Fusion (RRF)
create or replace function hybrid_search_chunks(
    query_text text,
    query_embedding vector(384),
    target_version text,
    match_count int,
    vector_weight float default 0.6,
    text_weight float default 0.4
)
returns table (
    id bigint,
    document_name text,
    section_title text,
    content text,
    final_score float
)
language plpgsql
as $$
begin
    return query
    with vector_matches as (
        select c.id, row_number() over (order by c.embedding <=> query_embedding) as rank
        from document_chunks c
        where c.version_id = target_version
        order by c.embedding <=> query_embedding
        limit match_count * 3
    ),
    text_matches as (
        select c.id, row_number() over (order by ts_rank(c.fts_tokens, plainto_tsquery('portuguese', query_text)) desc) as rank
        from document_chunks c
        where c.version_id = target_version
          and c.fts_tokens @@ plainto_tsquery('portuguese', query_text)
        order by ts_rank(c.fts_tokens, plainto_tsquery('portuguese', query_text)) desc
        limit match_count * 3
    )
    select 
        c.id,
        c.document_name,
        c.section_title,
        c.content,
        (
            coalesce(vector_weight * (1.0 / (60.0 + v.rank)), 0.0) +
            coalesce(text_weight * (1.0 / (60.0 + t.rank)), 0.0)
        )::float as final_score
    from document_chunks c
    left join vector_matches v on c.id = v.id
    left join text_matches t on c.id = t.id
    where (v.id is not null or t.id is not null)
      and c.version_id = target_version
    order by final_score desc
    limit match_count;
end;
$$;

-- 6. Configuração de Políticas de Segurança (Row Level Security - RLS)
alter table document_chunks enable row level security;
alter table rag_metadata enable row level security;

-- Remove políticas antigas se existirem para evitar conflitos de re-execução
drop policy if exists "Permitir leitura anonima de chunks" on document_chunks;
drop policy if exists "Permitir leitura anonima de metadata" on rag_metadata;
drop policy if exists "Permitir escrita apenas com service role chunks" on document_chunks;
drop policy if exists "Permitir escrita apenas com service role metadata" on rag_metadata;

-- Leitura pública segura (utilizada pelo Hugging Face Space com a anon_key)
create policy "Permitir leitura anonima de chunks" on document_chunks for select using (true);
create policy "Permitir leitura anonima de metadata" on rag_metadata for select using (true);

-- Escrita restrita (somente a service_role key do GitHub Actions pode inserir/atualizar)
create policy "Permitir escrita apenas com service role chunks" on document_chunks for all using (auth.role() = 'service_role');
create policy "Permitir escrita apenas com service role metadata" on rag_metadata for all using (auth.role() = 'service_role');
