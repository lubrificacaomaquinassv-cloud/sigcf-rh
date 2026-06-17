-- SIGCF — Cadastro RH (separado de dim_colaborador / Oficina)
-- Cole no SQL Editor do Supabase e clique Run (uma vez).

create table if not exists public.dim_rh (
    id bigint generated always as identity primary key,
    id_rh text not null unique,
    nome text not null,
    setor text,
    cargo text,
    ativo boolean not null default true,
    criado_em timestamptz not null default now()
);

create index if not exists idx_dim_rh_nome on public.dim_rh (nome);
create index if not exists idx_dim_rh_setor on public.dim_rh (setor);
create index if not exists idx_dim_rh_ativo on public.dim_rh (ativo) where ativo = true;

alter table public.dim_rh enable row level security;

drop policy if exists dim_rh_anon_all on public.dim_rh;
create policy dim_rh_anon_all on public.dim_rh
    for all using (true) with check (true);

comment on table public.dim_rh is 'SIGCF RH — cadastro de funcionários (Hub RH, absenteísmo, folha)';

-- Vincula justificativas à dim_rh (rode mesmo se a tabela de faltas já existir)
alter table public.rh_justificativa_faltas
    add column if not exists id_rh text;

create index if not exists idx_rh_faltas_id_rh on public.rh_justificativa_faltas (id_rh);

-- Exemplos — substitua pelos nomes reais do RH
insert into public.dim_rh (id_rh, nome, setor, cargo, ativo) values
('RH-0001', 'NOME COMPLETO FUNCIONARIO 1', 'Administração', 'Assistente administrativo', true),
('RH-0002', 'NOME COMPLETO FUNCIONARIO 2', 'Pecuária',       'Tratador', true),
('RH-0003', 'NOME COMPLETO FUNCIONARIO 3', 'Florestal',      'Operador florestal', true)
on conflict (id_rh) do update set
    nome = excluded.nome,
    setor = excluded.setor,
    cargo = excluded.cargo,
    ativo = excluded.ativo;

select setor, count(*) as qtd from dim_rh where ativo group by setor order by setor;
select id_rh, nome, setor, cargo from dim_rh where ativo order by nome;
