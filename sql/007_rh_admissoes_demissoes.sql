-- SIGRH — Contratações e demissões mensais (Relatório RH Admissão / Demissão)
-- Cole no SQL Editor do Supabase e clique Run (uma vez).

-- ---------------------------------------------------------------------------
-- 1) ADMISSÕES — contratações realizadas na competência
-- ---------------------------------------------------------------------------
create table if not exists public.rh_admissoes_mensal (
    id bigint generated always as identity primary key,
    id_rh text,
    competencia date not null,
    nome text not null,
    setor text,
    cargo text,
    cbo text,
    data_admissao date not null,
    matricula_esocial text,
    cpf text,
    sexo text,
    grau_instrucao text,
    origem text not null default 'IMPORT',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (nome, data_admissao)
);

create index if not exists idx_rh_adm_comp on public.rh_admissoes_mensal (competencia desc);
create index if not exists idx_rh_adm_setor on public.rh_admissoes_mensal (setor);
create index if not exists idx_rh_adm_id_rh on public.rh_admissoes_mensal (id_rh);

-- ---------------------------------------------------------------------------
-- 2) DEMISSÕES — rescisões realizadas na competência
-- ---------------------------------------------------------------------------
create table if not exists public.rh_demissoes_mensal (
    id bigint generated always as identity primary key,
    id_rh text,
    competencia date not null,
    nome text not null,
    setor text,
    cargo text,
    cbo text,
    data_admissao date,
    data_rescisao date not null,
    matricula_esocial text,
    cpf text,
    sexo text,
    origem text not null default 'IMPORT',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (nome, data_rescisao)
);

create index if not exists idx_rh_dem_comp on public.rh_demissoes_mensal (competencia desc);
create index if not exists idx_rh_dem_setor on public.rh_demissoes_mensal (setor);
create index if not exists idx_rh_dem_id_rh on public.rh_demissoes_mensal (id_rh);

alter table public.rh_admissoes_mensal enable row level security;
alter table public.rh_demissoes_mensal enable row level security;

drop policy if exists rh_admissoes_anon on public.rh_admissoes_mensal;
create policy rh_admissoes_anon on public.rh_admissoes_mensal for all using (true) with check (true);

drop policy if exists rh_demissoes_anon on public.rh_demissoes_mensal;
create policy rh_demissoes_anon on public.rh_demissoes_mensal for all using (true) with check (true);

comment on table public.rh_admissoes_mensal is 'SIGRH — contratações do mês (Relatório RH Admissão)';
comment on table public.rh_demissoes_mensal is 'SIGRH — demissões do mês (Relatório RH Demissão)';

select 'rh_admissoes_mensal' as tabela, count(*) as registros from rh_admissoes_mensal
union all select 'rh_demissoes_mensal', count(*) from rh_demissoes_mensal;
