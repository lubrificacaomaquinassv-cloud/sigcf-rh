-- SIGRH — Feedback da liderança
create table if not exists public.rh_feedback_lideranca (
    id bigint generated always as identity primary key,
    responsavel text not null,
    nome_lider_setor text,
    referente text,
    setor text,
    tipo_feedback text not null,
    opcao_registro text not null,
    descricao text not null,
    visita_rh text,
    criado_em timestamptz not null default now()
);

comment on table public.rh_feedback_lideranca is 'SIGRH — feedback da liderança (RH / gestores)';
