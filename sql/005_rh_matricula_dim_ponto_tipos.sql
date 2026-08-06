-- SIGRH — Matrícula FOPA em dim_rh + tipos de ponto para absenteísmo no painel
-- Rode UMA VEZ no Supabase.

alter table public.dim_rh
    add column if not exists matricula text;

create unique index if not exists idx_dim_rh_matricula
    on public.dim_rh (matricula)
    where matricula is not null and matricula <> '';

comment on column public.dim_rh.matricula is
  'Matrícula FOPA — igual a id_rh quando importado via PDF';

-- Tipos de ausência mensal (aba Absenteísmo do banco_horas_app)
create table if not exists public.rh_ponto_tipos_mensal (
    id bigint generated always as identity primary key,
    id_rh text not null,
    competencia date not null,
    setor text,
    tipo text not null,
    tipo_descricao text,
    qtd_dias numeric(6, 1) not null default 1,
    origem text not null default 'IMPORT_PDF',
    criado_em timestamptz not null default now(),
    unique (id_rh, competencia, tipo)
);

alter table public.rh_ponto_tipos_mensal enable row level security;
drop policy if exists rh_ponto_tipos_anon on public.rh_ponto_tipos_mensal;
create policy rh_ponto_tipos_anon on public.rh_ponto_tipos_mensal
    for all using (true) with check (true);

-- View dim_rh: join por id_rh OU matricula
create or replace view vw_rh_colaborador as
select
    coalesce(d.id_rh, d.matricula) as id_rh,
    d.nome,
    coalesce(d.setor, 'Outros') as setor,
    coalesce(d.cargo, '') as cargo,
    d.matricula,
    d.ativo
from dim_rh d
where coalesce(d.ativo, true) = true;
