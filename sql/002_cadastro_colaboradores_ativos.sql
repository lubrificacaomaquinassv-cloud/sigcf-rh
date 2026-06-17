-- SIGCF — Cadastro de colaboradores ativos (base RH + demais módulos)
-- Fonte única: dim_colaborador (ativo = true aparece no Hub RH, Apontamento, Oficina…)
--
-- 1) Cole no SQL Editor do Supabase
-- 2) Ajuste / acrescente linhas conforme planilha do RH
-- 3) funcao = setor/cargo resumido (ex.: PECUARIA, ADMINISTRATIVO, OPERADOR)
-- 4) custo_hora = 0 quando não for usado em cálculo de custo de frota

-- Colaboradores de exemplo (substitua pela lista real do RH)
insert into dim_colaborador (id_colaborador, nome, funcao, custo_hora, ativo) values
('RH-001', 'NOME COMPLETO FUNCIONARIO 1', 'ADMINISTRATIVO', 0, true),
('RH-002', 'NOME COMPLETO FUNCIONARIO 2', 'PECUARIA',       0, true),
('RH-003', 'NOME COMPLETO FUNCIONARIO 3', 'FLORESTAL',      0, true),
('RH-004', 'NOME COMPLETO FUNCIONARIO 4', 'REFEITORIO',     0, true),
('RH-005', 'NOME COMPLETO FUNCIONARIO 5', 'RH',             0, true)
on conflict (id_colaborador) do update set
    nome = excluded.nome,
    funcao = excluded.funcao,
    ativo = excluded.ativo;

-- Conferência
select funcao, count(*) as qtd
from dim_colaborador
where ativo = true
group by funcao
order by funcao;

select id_colaborador, nome, funcao, ativo
from dim_colaborador
where ativo = true
order by nome;
