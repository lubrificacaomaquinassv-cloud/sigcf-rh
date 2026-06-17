-- SIGCF — Módulo RH · Justificativa de Faltas
-- Cole no SQL Editor do Supabase e clique Run (uma vez).

create table if not exists public.rh_justificativa_faltas (
    id bigint generated always as identity primary key,
    data_falta date not null,
    id_colaborador text,
    nome_colaborador text not null,
    setor text,
    funcao text,
    tipo_justificativa text not null,
    dias_ausencia numeric(4,1) not null default 1,
    possui_atestado boolean not null default false,
    motivo text not null,
    observacao text,
    status text not null default 'REGISTRADO',
    registrado_por text,
    criado_em timestamptz not null default now()
);

create index if not exists idx_rh_faltas_data on public.rh_justificativa_faltas (data_falta desc);
create index if not exists idx_rh_faltas_colaborador on public.rh_justificativa_faltas (nome_colaborador);
create index if not exists idx_rh_faltas_setor on public.rh_justificativa_faltas (setor);

alter table public.rh_justificativa_faltas enable row level security;

drop policy if exists rh_faltas_anon_all on public.rh_justificativa_faltas;
create policy rh_faltas_anon_all on public.rh_justificativa_faltas
    for all using (true) with check (true);

comment on table public.rh_justificativa_faltas is 'SIGCF RH — justificativas de faltas e base para índice de absenteísmo';
