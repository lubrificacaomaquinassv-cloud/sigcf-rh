-- SIGRH — Detalhamento de tipos de justificativa/ausência (Absenteísmo)
-- Cole no SQL Editor do Supabase e clique Run (uma vez).
-- Uma linha por colaborador x tipo de ocorrência x competência (ex.: Atestado médico = 2 dias).

create table if not exists public.rh_ponto_tipos_mensal (
    id bigint generated always as identity primary key,
    id_rh text not null,
    competencia date not null,
    nome_colaborador text,
    setor text,
    tipo text not null,              -- código: FALTA_INJUSTIFICADA, ATESTADO_MEDICO, FERIAS, ...
    tipo_descricao text not null,    -- rótulo amigável: "Falta injustificada", "Atestado médico", ...
    qtd_dias numeric(6, 1) not null default 0,
    origem text not null default 'IMPORT',
    criado_em timestamptz not null default now(),
    unique (id_rh, competencia, tipo)
);

create index if not exists idx_rh_ponto_tipos_comp on public.rh_ponto_tipos_mensal (competencia desc);
create index if not exists idx_rh_ponto_tipos_setor on public.rh_ponto_tipos_mensal (setor);
create index if not exists idx_rh_ponto_tipos_tipo on public.rh_ponto_tipos_mensal (tipo);

alter table public.rh_ponto_tipos_mensal enable row level security;

drop policy if exists rh_ponto_tipos_anon on public.rh_ponto_tipos_mensal;
create policy rh_ponto_tipos_anon on public.rh_ponto_tipos_mensal for all using (true) with check (true);

comment on table public.rh_ponto_tipos_mensal is 'SIGRH — detalhamento de tipos de ausência/justificativa por colaborador e competência';

select 'rh_ponto_tipos_mensal' as tabela, count(*) as registros from rh_ponto_tipos_mensal;
