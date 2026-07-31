-- Importação contratações/demissões — competência 06/2026
-- Fonte: Relatorio RH_Admissão.Xls + Relatorio RH_Demissão.Xls
-- Rode após sql/007_rh_admissoes_demissoes.sql

delete from rh_admissoes_mensal where competencia = '2026-06-01';
delete from rh_demissoes_mensal where competencia = '2026-06-01';

insert into rh_admissoes_mensal (
    id_rh, competencia, nome, setor, cargo, cbo, data_admissao,
    matricula_esocial, cpf, sexo, grau_instrucao, origem
) values
(null, '2026-06-01', 'Igor Ribeiro Pereira', 'Sede / Pecuária', 'Vaqueiro', '6231-10', '2026-06-03', 'SESANTAVER00000000000000000566', '071.187.531-65', 'Masculino', '07 = Médio Completo', 'IMPORT'),
(null, '2026-06-01', 'Izamara dos Santos Nascimento', 'Almoxarifado', 'Aprendiz de Almoxarife', '4141-05', '2026-06-16', 'SESANTAVER00000000000000000568', '096.975.661-51', 'Feminino', '07 = Médio Completo', 'IMPORT'),
(null, '2026-06-01', 'Joao Pedro Medeiros', 'Retiro Poço Azul', 'Vaqueiro', '6231-10', '2026-06-18', 'SESANTAVER00000000000000000569', '058.480.251-00', 'Masculino', '06 = Médio Incompleto', 'IMPORT');

insert into rh_demissoes_mensal (
    id_rh, competencia, nome, setor, cargo, cbo, data_admissao, data_rescisao,
    matricula_esocial, cpf, sexo, origem
) values
('RH-0010', '2026-06-01', 'Alex Menegon de Lima', 'Plantio', 'Auxiliar Plantio(Aplic Def Agr', '6201-05', '2025-05-15', '2026-06-10', 'SESANTAVER00000000000000000491', '010.392.241-56', 'Masculino', 'IMPORT'),
('RH-0013', '2026-06-01', 'Ana Isa Almeida Vieira', 'Viveiro Florestal', 'Aux. Prod. Viveiro Mudas II', '6220-15', '2021-06-11', '2026-06-08', 'SESANTAVER00000000000000000154', '070.331.351-73', 'Feminino', 'IMPORT'),
('RH-0043', '2026-06-01', 'Ednilson Alexandre', 'Plantio', 'Auxiliar Plantio', '6201-05', '2025-11-03', '2026-06-01', 'SESANTAVER00000000000000000528', '049.262.114-40', 'Masculino', 'IMPORT'),
('RH-0059', '2026-06-01', 'Fernando Silva Nascimento', 'Plantio', 'Auxiliar Plantio', '6201-05', '2026-04-13', '2026-06-01', 'SESANTAVER00000000000000000557', '704.739.461-30', 'Masculino', 'IMPORT'),
('RH-0079', '2026-06-01', 'Jose Maria da Luz', 'Serviços Gerais', 'Serviços Gerais', '6210-05', '2023-08-15', '2026-06-10', 'SESANTAVER00000000000000000322', '032.038.034-37', 'Masculino', 'IMPORT'),
('RH-0096', '2026-06-01', 'Marcelo Lopes Siqueira', 'Plantio', 'Auxiliar Plantio', '6201-05', '2025-12-01', '2026-06-01', 'SESANTAVER00000000000000000536', '390.217.248-71', 'Masculino', 'IMPORT'),
('RH-0106', '2026-06-01', 'Matheus Alexandre da Silva', 'Sede / Pecuária', 'Vaqueiro', '6231-10', '2026-04-15', '2026-06-01', 'SESANTAVER00000000000000000558', '076.965.881-41', 'Masculino', 'IMPORT'),
('RH-0117', '2026-06-01', 'Paulo Junior dos Santos', 'Viveiro Florestal', 'Aux Prod Viveiro Mudas I(Aplic', '6220-15', '2024-10-22', '2026-06-10', 'SESANTAVER00000000000000000444', '016.092.661-02', 'Masculino', 'IMPORT'),
('RH-0126', '2026-06-01', 'Romario Fernandes Moreira', 'Plantio', 'Auxiliar Plantio', '6201-05', '2025-12-01', '2026-06-01', 'SESANTAVER00000000000000000535', '057.085.883-65', 'Masculino', 'IMPORT');

select 'admissoes' as tipo, count(*) from rh_admissoes_mensal where competencia = '2026-06-01'
union all select 'demissoes', count(*) from rh_demissoes_mensal where competencia = '2026-06-01';