-- SIGRH — Ponto diário (import cartão-ponto) + views para Lovable / Banco de Horas
-- Rode UMA VEZ no Supabase SQL Editor antes de importar os PDFs.

-- ---------------------------------------------------------------------------
-- 1) Eventos diários do cartão-ponto (faltas, férias, afastamentos, etc.)
-- ---------------------------------------------------------------------------
create table if not exists public.rh_ponto_dia (
    id bigint generated always as identity primary key,
    id_rh text not null,
    data date not null,
    competencia date not null,
    nome_colaborador text,
    setor text,
    cargo text,
    tipo_dia text not null,
    horas_abonadas numeric(8, 2) not null default 0,
    horas_debito numeric(8, 2) not null default 0,
    possui_atestado boolean not null default false,
    observacao text,
    origem text not null default 'IMPORT_PDF',
    criado_em timestamptz not null default now(),
    unique (id_rh, data, tipo_dia)
);

create index if not exists idx_rh_ponto_dia_data on public.rh_ponto_dia (data desc);
create index if not exists idx_rh_ponto_dia_comp on public.rh_ponto_dia (competencia desc);
create index if not exists idx_rh_ponto_dia_setor on public.rh_ponto_dia (setor);
create index if not exists idx_rh_ponto_dia_tipo on public.rh_ponto_dia (tipo_dia);

alter table public.rh_ponto_dia enable row level security;
drop policy if exists rh_ponto_dia_anon on public.rh_ponto_dia;
create policy rh_ponto_dia_anon on public.rh_ponto_dia for all using (true) with check (true);

comment on table public.rh_ponto_dia is
  'SIGRH — eventos diários do cartão-ponto (faltas, férias, exame periódico, etc.)';

-- ---------------------------------------------------------------------------
-- 2) Folha agregada por centro de custo (extrato analítico FOPA)
-- ---------------------------------------------------------------------------
create table if not exists public.rh_folha_setor (
    id bigint generated always as identity primary key,
    competencia date not null,
    codigo_cc text,
    setor text not null,
    qtd_colaboradores int not null default 0,
    total_proventos numeric(14, 2) not null default 0,
    total_descontos numeric(14, 2) not null default 0,
    total_liquido numeric(14, 2) not null default 0,
    total_folha numeric(14, 2) not null default 0,
    horas_he_50 numeric(12, 2) not null default 0,
    valor_he_50 numeric(14, 2) not null default 0,
    horas_he_100 numeric(12, 2) not null default 0,
    valor_he_100 numeric(14, 2) not null default 0,
    origem text not null default 'FOPA_CC',
    criado_em timestamptz not null default now(),
    unique (competencia, setor)
);

alter table public.rh_folha_setor enable row level security;
drop policy if exists rh_folha_setor_anon on public.rh_folha_setor;
create policy rh_folha_setor_anon on public.rh_folha_setor for all using (true) with check (true);

-- ---------------------------------------------------------------------------
-- 3) VIEW — acúmulo mensal por colaborador (horas + dias equivalentes)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_banco_horas_mes as
select
    b.competencia,
    to_char(b.competencia, 'YYYY-MM') as mes_key,
    b.id_rh,
    coalesce(d.nome, b.id_rh) as nome,
    coalesce(b.setor, d.setor, 'Outros') as setor,
    coalesce(d.cargo, '') as cargo,
    b.horas_he_50,
    b.horas_he_100,
    b.horas_credito,
    b.horas_debito,
    b.saldo_mes,
    b.saldo_acumulado,
    round(abs(coalesce(b.saldo_acumulado, b.saldo_mes, 0)) / 8.0, 2) as dias_equivalentes,
    b.valor_he_50,
    b.valor_he_100,
    b.valor_total,
    b.origem
from rh_banco_horas b
left join dim_rh d on d.id_rh = b.id_rh or d.matricula = b.id_rh;

comment on view vw_rh_banco_horas_mes is
  'Banco de horas mensal por colaborador com dias equivalentes (÷8h).';

-- ---------------------------------------------------------------------------
-- 4) VIEW — comparativo Jun × Jul (ou meses consecutivos)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_banco_horas_acumulo_jun_jul as
with meses as (
    select distinct competencia, to_char(competencia, 'YYYY-MM') as mes_key
    from rh_banco_horas
    order by competencia
),
pivot as (
    select
        id_rh,
        max(setor) as setor,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-06' then saldo_mes else 0 end) as saldo_jun,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-07' then saldo_mes else 0 end) as saldo_jul,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-06' then saldo_acumulado else 0 end) as acum_jun,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-07' then saldo_acumulado else 0 end) as acum_jul,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-06' then horas_he_50 else 0 end) as he50_jun,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-07' then horas_he_50 else 0 end) as he50_jul,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-06' then horas_he_100 else 0 end) as he100_jun,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-07' then horas_he_100 else 0 end) as he100_jul,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-06' then valor_total else 0 end) as valor_jun,
        sum(case when to_char(competencia, 'YYYY-MM') = '2026-07' then valor_total else 0 end) as valor_jul
    from rh_banco_horas
    where to_char(competencia, 'YYYY-MM') in ('2026-06', '2026-07')
    group by id_rh
)
select
    p.id_rh,
    coalesce(d.nome, p.id_rh) as nome,
    coalesce(p.setor, d.setor, 'Outros') as setor,
    coalesce(d.cargo, '') as cargo,
    p.saldo_jun,
    p.saldo_jul,
    round(p.saldo_jul - p.saldo_jun, 2) as variacao_saldo,
    p.acum_jun,
    p.acum_jul,
    p.he50_jun,
    p.he50_jul,
    p.he100_jun,
    p.he100_jul,
    p.valor_jun,
    p.valor_jul,
    round(coalesce(p.acum_jul, p.acum_jun, 0) / 8.0, 2) as dias_equivalentes_acum
from pivot p
left join dim_rh d on d.id_rh = p.id_rh or d.matricula = p.id_rh
order by coalesce(p.acum_jul, p.acum_jun, 0) desc;

comment on view vw_rh_banco_horas_acumulo_jun_jul is
  'Comparativo banco de horas Jun/2026 × Jul/2026 por colaborador.';

-- ---------------------------------------------------------------------------
-- 5) VIEW — setores ranqueados (maior saldo → menor)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_banco_horas_setor_rank as
select
    s.competencia,
    to_char(s.competencia, 'YYYY-MM') as mes_key,
    s.setor,
    s.qtd_colaboradores,
    s.horas_he_50,
    s.horas_he_100,
    s.horas_saldo_total,
    round(abs(s.horas_saldo_total) / 8.0, 2) as dias_equivalentes,
    s.valor_total,
    rank() over (
        partition by s.competencia
        order by abs(s.horas_saldo_total) desc
    ) as rank_saldo
from rh_banco_horas_setor s
order by s.competencia desc, abs(s.horas_saldo_total) desc;

comment on view vw_rh_banco_horas_setor_rank is
  'Setores ranqueados por saldo de banco de horas (maior → menor).';

-- ---------------------------------------------------------------------------
-- 6) VIEW — total empresa (valor + horas)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_banco_horas_empresa as
select
    competencia,
    to_char(competencia, 'YYYY-MM') as mes_key,
    count(distinct id_rh)::int as qtd_colaboradores,
    sum(horas_he_50)::numeric(12, 2) as horas_he_50_total,
    sum(horas_he_100)::numeric(12, 2) as horas_he_100_total,
    sum(horas_credito)::numeric(12, 2) as horas_credito_total,
    sum(horas_debito)::numeric(12, 2) as horas_debito_total,
    sum(saldo_mes)::numeric(12, 2) as saldo_mes_total,
    sum(coalesce(saldo_acumulado, saldo_mes))::numeric(14, 2) as saldo_acumulado_total,
    round(sum(coalesce(saldo_acumulado, saldo_mes)) / 8.0, 2) as dias_equivalentes_total,
    sum(valor_total)::numeric(14, 2) as valor_banco_total
from rh_banco_horas
group by competencia
order by competencia desc;

comment on view vw_rh_banco_horas_empresa is
  'Total consolidado do banco de horas da empresa por competência.';

-- ---------------------------------------------------------------------------
-- 7) VIEW — ausências do ponto (faltas, férias, exame, afastamentos)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_ponto_ausencias as
select
    p.competencia,
    to_char(p.competencia, 'YYYY-MM') as mes_key,
    p.id_rh,
    coalesce(p.nome_colaborador, d.nome, p.id_rh) as nome,
    coalesce(p.setor, d.setor, 'Outros') as setor,
    p.tipo_dia,
    count(*)::int as qtd_dias,
    sum(p.horas_abonadas)::numeric(10, 2) as horas_abonadas,
    sum(p.horas_debito)::numeric(10, 2) as horas_debito,
    bool_or(p.possui_atestado) as possui_atestado
from rh_ponto_dia p
left join dim_rh d on d.id_rh = p.id_rh or d.matricula = p.id_rh
where p.tipo_dia not in ('NORMAL', 'FOLGA', 'BANCO')
group by p.competencia, p.id_rh, p.nome_colaborador, p.setor, d.nome, d.setor, p.tipo_dia
order by p.competencia desc, qtd_dias desc;

comment on view vw_rh_ponto_ausencias is
  'Resumo de ausências por colaborador/tipo (cartão-ponto importado).';

-- ---------------------------------------------------------------------------
-- 8) VIEW — painel Lovable (consolidado)
-- ---------------------------------------------------------------------------
create or replace view vw_rh_banco_horas_painel as
select
    m.mes_key,
    m.competencia,
    m.id_rh,
    m.nome,
    m.setor,
    m.cargo,
    m.saldo_mes,
    m.saldo_acumulado,
    m.dias_equivalentes,
    m.horas_he_50,
    m.horas_he_100,
    m.valor_total,
    coalesce(a.qtd_faltas, 0) as dias_falta,
    coalesce(a.qtd_ferias, 0) as dias_ferias,
    coalesce(a.qtd_exame, 0) as dias_exame_periodico,
    coalesce(a.qtd_afastamento, 0) as dias_afastamento
from vw_rh_banco_horas_mes m
left join (
    select
        id_rh,
        competencia,
        sum(case when tipo_dia ilike '%FALTA%' then 1 else 0 end) as qtd_faltas,
        sum(case when tipo_dia ilike '%FERIAS%' or tipo_dia ilike '%FÉRIAS%' then 1 else 0 end) as qtd_ferias,
        sum(case when tipo_dia ilike '%EXAME%' then 1 else 0 end) as qtd_exame,
        sum(case when tipo_dia ilike '%AFAST%' then 1 else 0 end) as qtd_afastamento
    from rh_ponto_dia
    group by id_rh, competencia
) a on a.id_rh = m.id_rh and a.competencia = m.competencia
order by m.competencia desc, m.saldo_acumulado desc nulls last;

comment on view vw_rh_banco_horas_painel is
  'View única para Lovable — banco de horas + ausências do ponto.';

-- AUDITORIA
-- select * from vw_rh_banco_horas_empresa;
-- select * from vw_rh_banco_horas_setor_rank where mes_key = '2026-07';
-- select * from vw_rh_banco_horas_acumulo_jun_jul limit 20;
-- select * from vw_rh_banco_horas_painel limit 20;
