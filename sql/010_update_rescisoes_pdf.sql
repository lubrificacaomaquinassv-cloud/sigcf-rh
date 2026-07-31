-- Atualização de rescisões — gerado automaticamente dos PDFs locais
-- Rode após sql/009_rh_demissoes_rescisao_cols.sql

-- quitacao Ednilson, Assinado.pdf | EDNILSON ALEXANDRE | liquido R$ 7475.55
update rh_demissoes_mensal set
    causa_rescisao = 'Despedida sem justa causa, pelo empregador',
    codigo_afastamento = 'SJ2',
    data_aviso_previo = '2026-06-01',
    valor_liquido_rescisao = 7475.55
where cpf = '049.262.114-40' and data_rescisao = '2026-06-01';

-- quitacao Fernando, Assinado.pdf | FERNANDO SILVA NASCIMENTO | liquido R$ 1966.64
update rh_demissoes_mensal set
    causa_rescisao = 'Rescisão antecipada, pelo empregador, do contrato de trabalho por prazo determinado',
    codigo_afastamento = 'RA2',
    valor_liquido_rescisao = 1966.64
where cpf = '704.739.461-30' and data_rescisao = '2026-06-01';

-- quitacao Marcelo, Assinado.pdf | MARCELO LOPES SIQUEIRA | liquido R$ 3463.91
update rh_demissoes_mensal set
    causa_rescisao = 'Rescisão contratual a pedido do empregado',
    codigo_afastamento = 'SJ1',
    data_aviso_previo = '2026-06-01',
    valor_liquido_rescisao = 3463.91
where cpf = '390.217.248-71' and data_rescisao = '2026-06-01';

-- quitacao Romario, Assinado.pdf | ROMARIO FERNANDES MOREIRA | liquido R$ 6812.39
update rh_demissoes_mensal set
    causa_rescisao = 'Despedida sem justa causa, pelo empregador',
    codigo_afastamento = 'SJ2',
    data_aviso_previo = '2026-06-01',
    valor_liquido_rescisao = 6812.39
where cpf = '057.085.883-65' and data_rescisao = '2026-06-01';

-- Quitação_Alex Menegon, Assinado.pdf | ALEX MENEGON DE LIMA | liquido R$ 12673.36
update rh_demissoes_mensal set
    causa_rescisao = 'Despedida sem justa causa, pelo empregador',
    codigo_afastamento = 'SJ2',
    data_aviso_previo = '2026-06-10',
    valor_liquido_rescisao = 12673.36
where cpf = '010.392.241-56' and data_rescisao = '2026-06-10';

-- Quitação_Matheus Alexandre, Assinado.pdf | MATHEUS ALEXANDRE DA SILVA | liquido R$ 1258.23
update rh_demissoes_mensal set
    causa_rescisao = 'Rescisão contratual a pedido do empregado',
    codigo_afastamento = 'SJ1',
    data_aviso_previo = '2026-06-01',
    valor_liquido_rescisao = 1258.23
where cpf = '076.965.881-41' and data_rescisao = '2026-06-01';

select nome, data_rescisao, valor_liquido_rescisao, causa_rescisao from rh_demissoes_mensal where competencia = '2026-06-01' order by nome;