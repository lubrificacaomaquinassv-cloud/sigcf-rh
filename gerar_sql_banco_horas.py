# -*- coding: utf-8 -*-
"""Gera SQL de importação — Banco de horas, Folha (valor/hora) e Ponto/Absenteísmo.

Fontes (competência 06/2026 — período do cartão-ponto 21/05 a 20/06/2026):
  1. Controle Banco de Horas.xls   -> planilha de SALÁRIOS (Departamento, Nome, Função, Salário Base)
  2. Extrato Banco de Horas PDF    -> saldo do banco de horas e total gerado no período, por colaborador
  3. Cartão Ponto PDF (125 pág.)   -> registro diário -> classificação de absenteísmo
  4. sql/dim_rh_gerado.sql         -> mapa NOME -> id_rh / setor / cargo já cadastrado no SIGRH

Regras de absenteísmo (definidas com o RH da Santa Virgínia):
  - Qualquer dia com o código "Falta" = falta INJUSTIFICADA.
  - Dia útil sem nenhuma batida e sem nenhum código = falta INJUSTIFICADA (falha de registro).
  - Qualquer outro código (Folga, Banco, Dispensa Autorizada, Dispensa Ponto, Férias,
    Serviço Externo, Afastamento INSS, Folga Dia Util, Abonar quantidade de horas) = dia
    NÃO letivo/justificado -> não entra como falta e não entra no denominador de dias úteis.
  - "Atestado Médico" conta como falta JUSTIFICADA (entra em dias_falta, não em
    faltas_injustificadas) — EXCETO na data 11/06/2026: nessa data o código "Atestado Médico"
    é, na prática, o exame periódico obrigatório (toda 2ª quinta-feira do mês) e não representa
    uma ausência real -> é descartado por completo (não conta falta nem reduz dias úteis).
  - Domingo normalmente aparece como "Folga"; se o colaborador tiver batida de ponto no
    domingo (trabalhou), conta como dia trabalhado normalmente.

Saída: sql/004_import_banco_horas_202606.sql (colar no Supabase SQL Editor).
"""
from __future__ import annotations

import re
import sys
import unicodedata
from calendar import monthrange
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd
import pdfplumber

PASTA = Path(__file__).resolve().parent
SQL_DIM_RH = PASTA / "sql" / "dim_rh_gerado.sql"
SAIDA = PASTA / "sql" / "004_import_banco_horas_202606.sql"

ARQ_SALARIOS = Path(r"c:\Users\hmauricio\Desktop\Controle Banco de Horas.xls")
ARQ_EXTRATO = Path(r"c:\Users\hmauricio\Desktop\Extrato Banco de Horas_2105_20062026.PDF")
ARQ_PONTO = Path(r"c:\Users\hmauricio\Downloads\Cartão Ponto_2105_20062026.PDF")

COMPETENCIA = "2026-06-01"
DIVISOR_HORA_MES = 220  # jornada 44h/semana (seg-sex 8h + sáb 4h) -> divisor CLT padrão
DATA_EXAME_PERIODICO = "11/06/2026"  # toda 2ª quinta-feira do mês

# Colaboradores que não batem ponto no local (ex.: atendem residência/posto fora da fazenda)
# e por isso o cartão-ponto mostra "falta" o mês todo — não é ausência real. São excluídos
# do cálculo de absenteísmo (rh_ponto_mensal / rh_ponto_tipos_mensal) para não inflar os números.
EXCLUSAO_ABSENTEISMO = {
    "SILVANA MARIA DA SILVA",  # atende a casa do gerente na cidade, não bate ponto na fazenda
}

TIPO_KEYWORDS = (
    ("FOLGA DIA UTIL", "FOLGA_DIA_UTIL"),
    ("FOLGA", "FOLGA"),
    ("DISPENSA AUTORIZADA", "DISPENSA_AUTORIZADA"),
    ("DISPENSA PONTO", "DISPENSA_PONTO"),
    ("BANCO", "BANCO"),
    ("F�RIAS", "FERIAS"),
    ("FERIAS", "FERIAS"),
    ("SERVI�O EXTERNO", "SERVICO_EXTERNO"),
    ("SERVICO EXTERNO", "SERVICO_EXTERNO"),
    ("AFASTAMENTO INSS", "AFASTAMENTO_INSS"),
    ("ABONAR", "ABONO_HORAS"),
    ("SUSPENS", "SUSPENSAO"),
)

# Tipos exibidos como "justificativa de ausência" no painel de absenteísmo
# (exclui Folga/Banco/Trabalhado/Serviço Externo, que não são ausências).
TIPOS_JUSTIFICATIVA_ABSENTEISMO = {
    "FALTA_INJUSTIFICADA": "Falta injustificada",
    "ATESTADO_MEDICO": "Atestado médico",
    "FERIAS": "Férias",
    "AFASTAMENTO_INSS": "Afastamento INSS",
    "DISPENSA_AUTORIZADA": "Dispensa autorizada",
    "DISPENSA_PONTO": "Dispensa de ponto",
    "ABONO_HORAS": "Abono de horas",
    "SUSPENSAO": "Suspensão",
    "FOLGA_DIA_UTIL": "Folga em dia útil",
    "EXAME_PERIODICO": "Exame periódico (11/06)",
}


def norm(s) -> str:
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().upper()


def esc(v: str) -> str:
    return str(v).replace("'", "''")


# ---------------------------------------------------------------------------
# 1) dim_rh (id_rh / setor / cargo já cadastrados)
# ---------------------------------------------------------------------------
def carregar_dim_rh() -> dict:
    texto = SQL_DIM_RH.read_text(encoding="utf-8")
    linhas = re.findall(r"\('(RH-\d+)',\s*'((?:[^']|'')*)',\s*'((?:[^']|'')*)',\s*(?:'((?:[^']|'')*)'|null)", texto)
    out = {}
    for id_rh, nome, setor, cargo in linhas:
        nome_r = nome.replace("''", "'")
        out[norm(nome_r)] = {
            "id_rh": id_rh, "nome": nome_r,
            "setor": setor.replace("''", "'"), "cargo": (cargo or "").replace("''", "'"),
        }
    return out


# ---------------------------------------------------------------------------
# 2) Planilha de salários
# ---------------------------------------------------------------------------
def carregar_salarios(caminho: Path) -> dict:
    df = pd.read_excel(caminho, sheet_name=0, header=0)
    df = df.iloc[:, :4]
    df.columns = ["departamento", "nome", "funcao", "salario_base"]
    out = {}
    for _, row in df.iterrows():
        nome = str(row["nome"]).strip()
        if not nome or nome.lower() == "nan" or "total" in nome.lower():
            continue
        try:
            salario = float(row["salario_base"])
        except (TypeError, ValueError):
            continue
        out[norm(nome)] = {
            "nome": nome,
            "departamento": str(row["departamento"]).strip(),
            "funcao": str(row["funcao"]).strip(),
            "salario_base": salario,
            "valor_hora": round(salario / DIVISOR_HORA_MES, 2),
        }
    return out


# ---------------------------------------------------------------------------
# 3) Extrato Banco de Horas (saldo + total do período por colaborador)
#
# O relatório tem 5 colunas numéricas por linha (100%D, CRED/DEB, AJUSTE,
# TOTAL, SALDO), mas colunas com valor zero simplesmente não são impressas.
# Extrair pela ORDEM dos números impressos (ex.: "pegar os 2 últimos") é
# ambíguo quando SALDO (ou TOTAL) vem em branco — nesse caso o penúltimo
# número impresso não é necessariamente TOTAL, e o último não é SALDO.
# Por isso usamos a posição (x) de cada número na página, comparada com a
# posição de cada cabeçalho de coluna, para atribuir cada valor à coluna
# correta — TOTAL = CRED/DEB + AJUSTE quando a coluna TOTAL vier em branco.
# ---------------------------------------------------------------------------
RE_NUM_HHMM = re.compile(r"-?\d{1,4}:\d{2}")
RE_NOME_MATRICULA = re.compile(r"^([A-ZÀ-Ü' .]+?)\s+(\d{1,6})\b")
COLUNAS_HEADER = ("CRED/DEB", "AJUSTE", "TOTAL", "SALDO")


def hhmm_para_min(s: str) -> int:
    neg = s.startswith("-")
    h, m = s.lstrip("-").split(":")
    v = int(h) * 60 + int(m)
    return -v if neg else v


def _limites_colunas(pdf) -> dict:
    """Usa a linha de cabeçalho (NOME ... 100%D CRED/DEB AJUSTE TOTAL SALDO) para
    descobrir a faixa de x de cada coluna. Não basta buscar a palavra "TOTAL" solta
    na página, pois ela também aparece em cada linha de subtotal por setor."""
    centros = {}
    for page in pdf.pages:
        palavras = page.extract_words()
        linhas = {}
        for w in palavras:
            linhas.setdefault(round(w["top"]), []).append(w)
        for ws in linhas.values():
            achados = {w["text"]: (w["x0"] + w["x1"]) / 2 for w in ws if w["text"] in COLUNAS_HEADER}
            if len(achados) == len(COLUNAS_HEADER):
                centros = achados
                break
        if centros:
            break
    if not centros:
        # fallback com posições típicas observadas no layout padrão do relatório
        centros = {"CRED/DEB": 654.0, "AJUSTE": 703.0, "TOTAL": 749.0, "SALDO": 795.0}
    ordem = sorted(centros.items(), key=lambda kv: kv[1])
    limites = {}
    for i, (nome, centro) in enumerate(ordem):
        lo = -1e9 if i == 0 else (ordem[i - 1][1] + centro) / 2
        hi = 1e9 if i == len(ordem) - 1 else (centro + ordem[i + 1][1]) / 2
        limites[nome] = (lo, hi)
    return limites


def carregar_extrato(caminho: Path) -> dict:
    resultados = {}
    with pdfplumber.open(caminho) as pdf:
        limites = _limites_colunas(pdf)

        def coluna_de(x0):
            for nome, (lo, hi) in limites.items():
                if lo <= x0 < hi:
                    return nome
            return None

        for page in pdf.pages:
            palavras = page.extract_words()
            if not palavras:
                continue
            linhas = {}
            for w in palavras:
                linhas.setdefault(round(w["top"]), []).append(w)
            for top in sorted(linhas):
                ws = sorted(linhas[top], key=lambda w: w["x0"])
                texto = " ".join(w["text"] for w in ws)
                up = texto.upper()
                if up.startswith("TOTAL") or any(p in up for p in SKIP_HEADERS) or RE_SKIP_PERIODO.match(up):
                    continue
                m = RE_NOME_MATRICULA.match(texto)
                if not m:
                    continue
                nome, matricula = m.group(1).strip(), m.group(2)
                if norm(nome) == "ADMINISTRADOR":
                    continue
                valores = {}
                for w in ws:
                    if RE_NUM_HHMM.fullmatch(w["text"]):
                        col = coluna_de((w["x0"] + w["x1"]) / 2)
                        if col:
                            valores[col] = w["text"]
                if "TOTAL" in valores:
                    total_min = hhmm_para_min(valores["TOTAL"])
                else:
                    total_min = hhmm_para_min(valores.get("CRED/DEB", "0:00")) + hhmm_para_min(valores.get("AJUSTE", "0:00"))
                saldo_min = hhmm_para_min(valores["SALDO"]) if "SALDO" in valores else 0
                resultados[norm(nome)] = {
                    "nome": nome, "matricula": matricula, "cargo": "", "departamento": "",
                    "total_mes_h": round(total_min / 60, 2), "saldo_h": round(saldo_min / 60, 2),
                }
    return resultados


RE_SKIP_PERIODO = re.compile(r"^DE\s+\d{2}/\d{2}/\d{4}\s+AT")
SKIP_HEADERS = ("EMITIDO EM", "EXTRATO POR PER", "N�MERO DE EXTRA", "NOME DO FUNCION", "P�GINA", "FUNCION�RIOS")


# ---------------------------------------------------------------------------
# 4) Cartão Ponto -> absenteísmo
# ---------------------------------------------------------------------------
RE_HEADER_NOME = re.compile(r"NOME DO FUNCION.RIO:\s*(.+?)\s+N.MERO DE MATR.CULA:\s*(\d+)")
RE_HEADER_CARGO = re.compile(r"NOME DO CARGO:\s*(.+?)\s+NOME DO DEPARTAMENTO:\s*(.+?)\s+ENT")
RE_DIA = re.compile(r"^(\d{2}/\d{2}/\d{4}) - (\w{3})\s*(.*)$")


def classificar_dia(data_str: str, resto: str) -> str:
    resto_up = resto.upper()
    if "FALTA" in resto_up:
        return "FALTA_INJUSTIFICADA"
    if "ATESTADO" in resto_up:
        return "EXAME_PERIODICO" if data_str == DATA_EXAME_PERIODICO else "ATESTADO_MEDICO"
    for kw, tipo in TIPO_KEYWORDS:
        if kw in resto_up:
            return tipo
    tem_hora = bool(RE_NUM_HHMM.search(resto))
    if tem_hora:
        return "TRABALHADO"
    return "FALTA_INJUSTIFICADA"  # dia útil sem batida e sem código


def carregar_ponto(caminho: Path) -> dict:
    out = {}
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            m_nome = RE_HEADER_NOME.search(txt)
            if not m_nome:
                continue
            nome, matricula = m_nome.group(1).strip(), m_nome.group(2).strip()
            if norm(nome) == "ADMINISTRADOR":
                continue
            m_cargo = RE_HEADER_CARGO.search(txt)
            cargo = m_cargo.group(1).strip() if m_cargo else ""
            departamento = m_cargo.group(2).strip() if m_cargo else ""

            contagem = defaultdict(int)
            dias_uteis_esperados = 0
            for line in txt.split("\n"):
                m = RE_DIA.match(line.strip())
                if not m:
                    continue
                data_str, dow, resto = m.groups()
                classe = classificar_dia(data_str, resto)
                contagem[classe] += 1
                if classe in ("TRABALHADO", "SERVICO_EXTERNO", "FALTA_INJUSTIFICADA", "ATESTADO_MEDICO"):
                    dias_uteis_esperados += 1

            dias_justificados_total = sum(
                n for tipo, n in contagem.items() if tipo in TIPOS_JUSTIFICATIVA_ABSENTEISMO
            )
            out[norm(nome)] = {
                "nome": nome, "matricula": matricula, "cargo": cargo, "departamento": departamento,
                "dias_uteis": dias_uteis_esperados,
                "dias_trabalhados": contagem["TRABALHADO"] + contagem["SERVICO_EXTERNO"],
                "faltas_injustificadas": contagem["FALTA_INJUSTIFICADA"],
                "atestado_medico": contagem["ATESTADO_MEDICO"],
                "dias_falta": contagem["FALTA_INJUSTIFICADA"] + contagem["ATESTADO_MEDICO"],
                "exame_periodico": contagem["EXAME_PERIODICO"],
                "dias_justificados": dias_justificados_total,
                "tipos": {tipo: n for tipo, n in contagem.items() if tipo in TIPOS_JUSTIFICATIVA_ABSENTEISMO},
            }
    return out


# ---------------------------------------------------------------------------
# Montagem final + SQL
# ---------------------------------------------------------------------------
def main():
    print("Carregando dim_rh...")
    dim_rh = carregar_dim_rh()
    print(f"  {len(dim_rh)} colaboradores cadastrados")

    print("Carregando planilha de salários...")
    salarios = carregar_salarios(ARQ_SALARIOS)
    print(f"  {len(salarios)} colaboradores com salário")

    print("Lendo Extrato Banco de Horas (PDF)...")
    extrato = carregar_extrato(ARQ_EXTRATO)
    print(f"  {len(extrato)} colaboradores no extrato")

    print("Lendo Cartão Ponto (PDF, 125 páginas — pode levar ~2 min)...")
    ponto = carregar_ponto(ARQ_PONTO)
    print(f"  {len(ponto)} colaboradores no cartão-ponto")

    todos_nomes = set(dim_rh) | set(salarios) | set(extrato) | set(ponto)
    nao_cadastrados = sorted(n for n in todos_nomes if n not in dim_rh)
    if nao_cadastrados:
        print(f"\nAVISO: {len(nao_cadastrados)} nome(s) sem correspondência em dim_rh (ignorados na saída):")
        for n in nao_cadastrados[:15]:
            print("   -", n)

    linhas_banco, linhas_folha, linhas_ponto, linhas_tipos = [], [], [], []
    ids_excluidos_absenteismo = []
    setor_agg = defaultdict(lambda: {"qtd": 0, "he50": 0.0, "he100": 0.0, "saldo": 0.0, "valor": 0.0})

    for nrm in sorted(todos_nomes & set(dim_rh)):
        rh = dim_rh[nrm]
        id_rh, setor, cargo = rh["id_rh"], rh["setor"], rh["cargo"] or None
        sal = salarios.get(nrm)
        ext = extrato.get(nrm)
        pto = ponto.get(nrm)

        valor_hora = sal["valor_hora"] if sal else None

        if ext:
            saldo_h = ext["saldo_h"]
            total_mes_h = ext["total_mes_h"]
            valor_total = round((valor_hora or 0) * saldo_h, 2)
            linhas_banco.append(
                f"('{id_rh}', '{COMPETENCIA}', '{esc(setor)}', 0, 0, "
                f"{max(total_mes_h, 0)}, {abs(min(total_mes_h, 0))}, {total_mes_h}, {saldo_h}, "
                f"0, 0, {valor_total}, 'IMPORT_FOPA', "
                f"'Extrato banco de horas 21/05-20/06/2026')"
            )
            setor_agg[setor]["qtd"] += 1
            setor_agg[setor]["saldo"] += saldo_h
            setor_agg[setor]["valor"] += valor_total

        if sal:
            bruto = sal["salario_base"]
            linhas_folha.append(
                f"('{id_rh}', '{COMPETENCIA}', '{esc(setor)}', '{esc(sal['funcao'])}', "
                f"{bruto}, 0, 0, {bruto}, {sal['valor_hora']}, 'IMPORT_PLANILHA', "
                f"'Controle Banco de Horas.xls')"
            )

        if nrm in EXCLUSAO_ABSENTEISMO:
            ids_excluidos_absenteismo.append(id_rh)
        elif pto:
            obs_ponto = (
                f"Justificados={pto['dias_justificados']}; "
                f"Exame periodico(11/06)={pto['exame_periodico']}; "
                f"Atestado medico (falta justificada)={pto['atestado_medico']}"
            )
            linhas_ponto.append(
                f"('{id_rh}', '{COMPETENCIA}', '{esc(rh['nome'])}', '{esc(setor)}', "
                f"{pto['dias_uteis']}, {pto['dias_trabalhados']}, {pto['dias_falta']}, 0, "
                f"0, 0, 0, {pto['faltas_injustificadas']}, 'IMPORT_CARTAO_PONTO', "
                f"'{esc(obs_ponto)}')"
            )
            for tipo, qtd in pto["tipos"].items():
                if qtd <= 0:
                    continue
                linhas_tipos.append(
                    f"('{id_rh}', '{COMPETENCIA}', '{esc(rh['nome'])}', '{esc(setor)}', "
                    f"'{tipo}', '{esc(TIPOS_JUSTIFICATIVA_ABSENTEISMO[tipo])}', {qtd}, "
                    f"'IMPORT_CARTAO_PONTO')"
                )

    partes = [
        f"-- Importação SIGRH — competência {COMPETENCIA[:7]} "
        f"(cartão-ponto 21/05 a 20/06/2026)\n"
        f"-- Gerado automaticamente por gerar_sql_banco_horas.py — cole no Supabase SQL Editor.\n",
    ]

    if ids_excluidos_absenteismo:
        ids_sql = ", ".join(f"'{i}'" for i in ids_excluidos_absenteismo)
        partes.append(
            f"\n-- Colaboradores excluídos do calculo de absenteísmo (não batem ponto no local): {ids_sql}\n"
            f"delete from rh_ponto_mensal where competencia = '{COMPETENCIA}' and id_rh in ({ids_sql});\n"
            f"delete from rh_ponto_tipos_mensal where competencia = '{COMPETENCIA}' and id_rh in ({ids_sql});\n"
        )

    if linhas_banco:
        partes.append(
            "insert into rh_banco_horas (id_rh, competencia, setor, horas_he_50, horas_he_100, "
            "horas_credito, horas_debito, saldo_mes, saldo_acumulado, valor_he_50, valor_he_100, "
            "valor_total, origem, observacao) values\n" + ",\n".join(linhas_banco) +
            "\non conflict (id_rh, competencia) do update set\n"
            "  setor = excluded.setor, horas_credito = excluded.horas_credito, "
            "horas_debito = excluded.horas_debito, saldo_mes = excluded.saldo_mes, "
            "saldo_acumulado = excluded.saldo_acumulado, valor_total = excluded.valor_total, "
            "origem = excluded.origem, observacao = excluded.observacao;\n"
        )

    if linhas_folha:
        partes.append(
            "\ninsert into rh_folha_mensal (id_rh, competencia, setor, cargo, salario_bruto, "
            "encargos_empresa, descontos, salario_liquido, valor_hora_ref, origem, observacao) values\n"
            + ",\n".join(linhas_folha) +
            "\non conflict (id_rh, competencia) do update set\n"
            "  setor = excluded.setor, cargo = excluded.cargo, salario_bruto = excluded.salario_bruto, "
            "salario_liquido = excluded.salario_liquido, valor_hora_ref = excluded.valor_hora_ref, "
            "origem = excluded.origem, observacao = excluded.observacao;\n"
        )

    if linhas_ponto:
        partes.append(
            "\ninsert into rh_ponto_mensal (id_rh, competencia, nome_colaborador, setor, dias_uteis, "
            "dias_trabalhados, dias_falta, dias_atraso, horas_previstas, horas_realizadas, "
            "minutos_atraso, faltas_injustificadas, origem, observacao) values\n"
            + ",\n".join(linhas_ponto) +
            "\non conflict (id_rh, competencia) do update set\n"
            "  nome_colaborador = excluded.nome_colaborador, setor = excluded.setor, "
            "dias_uteis = excluded.dias_uteis, dias_trabalhados = excluded.dias_trabalhados, "
            "dias_falta = excluded.dias_falta, faltas_injustificadas = excluded.faltas_injustificadas, "
            "origem = excluded.origem, observacao = excluded.observacao;\n"
        )

    if linhas_tipos:
        partes.append(
            "\ndelete from rh_ponto_tipos_mensal where competencia = '" + COMPETENCIA + "';\n"
            "insert into rh_ponto_tipos_mensal (id_rh, competencia, nome_colaborador, setor, "
            "tipo, tipo_descricao, qtd_dias, origem) values\n"
            + ",\n".join(linhas_tipos) + ";\n"
        )

    linhas_setor = []
    for setor, agg in sorted(setor_agg.items(), key=lambda kv: kv[1]["saldo"], reverse=True):
        linhas_setor.append(
            f"('{COMPETENCIA}', '{esc(setor)}', {agg['qtd']}, {round(agg['he50'], 2)}, "
            f"{round(agg['he100'], 2)}, {round(agg['saldo'], 2)}, {round(agg['valor'], 2)}, "
            f"'IMPORT_FOPA', 'Agregado do extrato 21/05-20/06/2026')"
        )
    if linhas_setor:
        partes.append(
            "\ninsert into rh_banco_horas_setor (competencia, setor, qtd_colaboradores, horas_he_50, "
            "horas_he_100, horas_saldo_total, valor_total, origem, observacao) values\n"
            + ",\n".join(linhas_setor) +
            "\non conflict (competencia, setor) do update set\n"
            "  qtd_colaboradores = excluded.qtd_colaboradores, horas_saldo_total = excluded.horas_saldo_total, "
            "valor_total = excluded.valor_total, origem = excluded.origem, observacao = excluded.observacao;\n"
        )

    SAIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"\nOK -> {SAIDA}")
    print(f"  rh_banco_horas: {len(linhas_banco)} linhas")
    print(f"  rh_folha_mensal: {len(linhas_folha)} linhas")
    print(f"  rh_ponto_mensal: {len(linhas_ponto)} linhas")
    print(f"  rh_ponto_tipos_mensal: {len(linhas_tipos)} linhas")
    print(f"  rh_banco_horas_setor: {len(linhas_setor)} setores")


if __name__ == "__main__":
    main()
