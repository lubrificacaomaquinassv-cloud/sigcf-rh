-- SIGRH — Banco de horas, Folha, Ponto (Fase 2)
-- Cole no SQL Editor do Supabase e clique Run (uma vez).

-- ---------------------------------------------------------------------------
-- 1) BANCO DE HORAS — individual (colaborador × competência)
--    Campos alinhados à planilha FOPA: HE 50%, HE 100%, saldo, valores
-- ---------------------------------------------------------------------------
create table if not exists public.rh_banco_horas (
    id bigint generated always as identity primary key,
    id_rh text not null,
    competencia date not null,
    setor text,
    horas_he_50 numeric(10, 2) not null default 0,
    horas_he_100 numeric(10, 2) not null default 0,
    horas_credito numeric(10, 2) not null default 0,
    horas_debito numeric(10, 2) not null default 0,
    saldo_mes numeric(10, 2) not null default 0,
    saldo_acumulado numeric(12, 2),
    valor_he_50 numeric(14, 2) not null default 0,
    valor_he_100 numeric(14, 2) not null default 0,
    valor_total numeric(14, 2) not null default 0,
    origem text not null default 'MANUAL',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (id_rh, competencia)
);

create index if not exists idx_rh_banco_comp on public.rh_banco_horas (competencia desc);
create index if not exists idx_rh_banco_setor on public.rh_banco_horas (setor);
create index if not exists idx_rh_banco_id_rh on public.rh_banco_horas (id_rh);

-- ---------------------------------------------------------------------------
-- 2) BANCO DE HORAS — resumo por SETOR (Saldo FOPA mensal agregado)
-- ---------------------------------------------------------------------------
create table if not exists public.rh_banco_horas_setor (
    id bigint generated always as identity primary key,
    competencia date not null,
    setor text not null,
    qtd_colaboradores int not null default 0,
    horas_he_50 numeric(12, 2) not null default 0,
    horas_he_100 numeric(12, 2) not null default 0,
    horas_saldo_total numeric(12, 2) not null default 0,
    valor_total numeric(14, 2) not null default 0,
    origem text not null default 'FOPA',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (competencia, setor)
);

create index if not exists idx_rh_banco_setor_comp on public.rh_banco_horas_setor (competencia desc);

-- ---------------------------------------------------------------------------
-- 3) FOLHA — salários e encargos individual (bruto / líquido)
-- ---------------------------------------------------------------------------
create table if not exists public.rh_folha_mensal (
    id bigint generated always as identity primary key,
    id_rh text not null,
    competencia date not null,
    setor text,
    cargo text,
    salario_bruto numeric(14, 2) not null default 0,
    encargos_empresa numeric(14, 2) not null default 0,
    descontos numeric(14, 2) not null default 0,
    salario_liquido numeric(14, 2) not null default 0,
    valor_hora_ref numeric(10, 2),
    origem text not null default 'MANUAL',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (id_rh, competencia)
);

create index if not exists idx_rh_folha_comp on public.rh_folha_mensal (competencia desc);
create index if not exists idx_rh_folha_setor on public.rh_folha_mensal (setor);

-- ---------------------------------------------------------------------------
-- 4) PONTO — resumo mensal por colaborador (import relatório de ponto)
-- ---------------------------------------------------------------------------
create table if not exists public.rh_ponto_mensal (
    id bigint generated always as identity primary key,
    id_rh text not null,
    competencia date not null,
    nome_colaborador text,
    setor text,
    dias_uteis int not null default 22,
    dias_trabalhados numeric(6, 1) not null default 0,
    dias_falta numeric(6, 1) not null default 0,
    dias_atraso numeric(6, 1) not null default 0,
    horas_previstas numeric(10, 2) not null default 0,
    horas_realizadas numeric(10, 2) not null default 0,
    minutos_atraso int not null default 0,
    faltas_injustificadas numeric(6, 1) not null default 0,
    origem text not null default 'IMPORT',
    observacao text,
    criado_em timestamptz not null default now(),
    unique (id_rh, competencia)
);

create index if not exists idx_rh_ponto_comp on public.rh_ponto_mensal (competencia desc);
create index if not exists idx_rh_ponto_setor on public.rh_ponto_mensal (setor);

-- RLS (mesmo padrão SIGRH)
alter table public.rh_banco_horas enable row level security;
alter table public.rh_banco_horas_setor enable row level security;
alter table public.rh_folha_mensal enable row level security;
alter table public.rh_ponto_mensal enable row level security;

drop policy if exists rh_banco_horas_anon on public.rh_banco_horas;
create policy rh_banco_horas_anon on public.rh_banco_horas for all using (true) with check (true);

drop policy if exists rh_banco_setor_anon on public.rh_banco_horas_setor;
create policy rh_banco_setor_anon on public.rh_banco_horas_setor for all using (true) with check (true);

drop policy if exists rh_folha_anon on public.rh_folha_mensal;
create policy rh_folha_anon on public.rh_folha_mensal for all using (true) with check (true);

drop policy if exists rh_ponto_anon on public.rh_ponto_mensal;
create policy rh_ponto_anon on public.rh_ponto_mensal for all using (true) with check (true);

comment on table public.rh_banco_horas is 'SIGRH — banco de horas individual (HE 50/100, saldo, valor)';
comment on table public.rh_banco_horas_setor is 'SIGRH — resumo FOPA banco de horas por setor';
comment on table public.rh_folha_mensal is 'SIGRH — folha mensal bruto/líquido/encargos';
comment on table public.rh_ponto_mensal is 'SIGRH — resumo ponto mensal para absenteísmo';

-- Competência exemplo: jun/2026 (Saldo FOPA)
-- insert into rh_banco_horas_setor (competencia, setor, qtd_colaboradores, horas_he_50, horas_he_100, horas_saldo_total, valor_total)
-- values ('2026-06-01', 'Máquinas', 0, 0, 0, 0, 0);

select 'rh_banco_horas' as tabela, count(*) as registros from rh_banco_horas
union all select 'rh_banco_horas_setor', count(*) from rh_banco_horas_setor
union all select 'rh_folha_mensal', count(*) from rh_folha_mensal
union all select 'rh_ponto_mensal', count(*) from rh_ponto_mensal;
