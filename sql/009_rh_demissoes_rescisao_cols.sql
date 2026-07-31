-- SIGRH — Campos de rescisão (Termo de Quitação / TRCT) em rh_demissoes_mensal
-- Rode após sql/007_rh_admissoes_demissoes.sql

alter table public.rh_demissoes_mensal
    add column if not exists causa_rescisao text,
    add column if not exists codigo_afastamento text,
    add column if not exists data_aviso_previo date,
    add column if not exists valor_liquido_rescisao numeric(14, 2),
    add column if not exists valor_bruto_rescisao numeric(14, 2);

comment on column public.rh_demissoes_mensal.causa_rescisao is 'Motivo da rescisão (campo 22 do termo de quitação)';
comment on column public.rh_demissoes_mensal.codigo_afastamento is 'Código eSocial/Sefip (ex.: RA2, JC2)';
comment on column public.rh_demissoes_mensal.valor_liquido_rescisao is 'Valor líquido pago na rescisão (termo de quitação)';
