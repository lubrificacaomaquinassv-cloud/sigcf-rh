# -*- coding: utf-8 -*-
"""Gera SQL de importação — Contratações e Demissões mensais.

Fontes (Relatório RH exportado do sistema de folha):
  - Relatorio RH_Admissão.Xls  -> rh_admissoes_mensal
  - Relatorio RH_Demissão.Xls  -> rh_demissoes_mensal
  - sql/dim_rh_gerado.sql      -> mapa NOME -> id_rh

Uso:
  python gerar_sql_admissoes_demissoes.py
  python gerar_sql_admissoes_demissoes.py 2026 6

Saída: sql/008_import_admissoes_demissoes_YYYYMM.sql
"""
from __future__ import annotations

import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
SQL_DIM_RH = PASTA / "sql" / "dim_rh_gerado.sql"

ARQ_ADMISSAO = Path(r"c:\Users\hmauricio\Desktop\RH\Relatorio RH_Admissão.Xls")
ARQ_DEMISSAO = Path(r"c:\Users\hmauricio\Desktop\RH\Relatorio RH_Demissão.Xls")

COLUNAS = [
    "setor", "nome", "cargo", "cbo", "data_admissao", "data_rescisao",
    "matricula_esocial", "pis", "sexo", "grau_instrucao", "cpf",
]


def norm(s) -> str:
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().upper()


def esc(v: str) -> str:
    return str(v).replace("'", "''")


def sql_val(v, tipo="text") -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "null"
    if tipo == "date":
        if isinstance(v, (datetime, date, pd.Timestamp)):
            return f"'{v.strftime('%Y-%m-%d')}'"
        s = str(v).strip()
        if not s or s.lower() == "nan":
            return "null"
        try:
            dt = pd.to_datetime(s)
            return f"'{dt.strftime('%Y-%m-%d')}'"
        except Exception:
            return "null"
    s = str(v).strip()
    if not s or s.lower() == "nan":
        return "null"
    return f"'{esc(s)}'"


def carregar_dim_rh() -> dict:
    texto = SQL_DIM_RH.read_text(encoding="utf-8")
    linhas = re.findall(
        r"\('(RH-\d+)',\s*'((?:[^']|'')*)',\s*'((?:[^']|'')*)',\s*(?:'((?:[^']|'')*)'|null)",
        texto,
    )
    out = {}
    for id_rh, nome, setor, cargo in linhas:
        nome_r = nome.replace("''", "'")
        out[norm(nome_r)] = {
            "id_rh": id_rh,
            "nome": nome_r,
            "setor": setor.replace("''", "'"),
            "cargo": (cargo or "").replace("''", "'"),
        }
    return out


def ler_relatorio(caminho: Path) -> pd.DataFrame:
    df = pd.read_excel(caminho, sheet_name=0, header=0)
    ncols = min(len(COLUNAS), df.shape[1])
    df = df.iloc[:, :ncols].copy()
    df.columns = COLUNAS[:ncols]
    return df


def linha_valida(row) -> bool:
    nome = str(row.get("nome", "")).strip()
    if not nome or nome.lower() == "nan":
        return False
    nome_norm = norm(nome)
    if any(x in nome_norm for x in ("TOTAL", "REGISTRO", "SOMA", "SUBTOTAL")):
        return False
    return True


def competencia_de_data(dt_val, ano: int, mes: int) -> bool:
    if dt_val is None or (isinstance(dt_val, float) and pd.isna(dt_val)):
        return False
    try:
        dt = pd.to_datetime(dt_val)
    except Exception:
        return False
    return dt.year == ano and dt.month == mes


def main():
    if len(sys.argv) >= 3:
        ano, mes = int(sys.argv[1]), int(sys.argv[2])
    else:
        ano, mes = 2026, 6

    competencia = f"{ano:04d}-{mes:02d}-01"
    saida = PASTA / "sql" / f"008_import_admissoes_demissoes_{ano}{mes:02d}.sql"

    if not ARQ_ADMISSAO.is_file():
        sys.exit(f"Arquivo não encontrado: {ARQ_ADMISSAO}")
    if not ARQ_DEMISSAO.is_file():
        sys.exit(f"Arquivo não encontrado: {ARQ_DEMISSAO}")
    if not SQL_DIM_RH.is_file():
        sys.exit(f"Arquivo não encontrado: {SQL_DIM_RH}")

    dim_rh = carregar_dim_rh()
    print(f"dim_rh: {len(dim_rh)} colaboradores")

    df_adm = ler_relatorio(ARQ_ADMISSAO)
    df_dem = ler_relatorio(ARQ_DEMISSAO)

    linhas_adm = []
    linhas_dem = []
    nao_cadastrados = set()

    for _, row in df_adm.iterrows():
        if not linha_valida(row):
            continue
        if not competencia_de_data(row["data_admissao"], ano, mes):
            continue
        nome = str(row["nome"]).strip()
        nrm = norm(nome)
        id_rh = dim_rh[nrm]["id_rh"] if nrm in dim_rh else None
        if not id_rh:
            nao_cadastrados.add(nome)
        setor = str(row["setor"]).strip() if str(row["setor"]) != "nan" else ""
        cargo = str(row["cargo"]).strip() if str(row["cargo"]) != "nan" else ""
        linhas_adm.append(
            f"({sql_val(id_rh)}, '{competencia}', {sql_val(nome)}, {sql_val(setor)}, "
            f"{sql_val(cargo)}, {sql_val(row.get('cbo'))}, {sql_val(row['data_admissao'], 'date')}, "
            f"{sql_val(row.get('matricula_esocial'))}, {sql_val(row.get('cpf'))}, "
            f"{sql_val(row.get('sexo'))}, {sql_val(row.get('grau_instrucao'))}, 'IMPORT')"
        )

    for _, row in df_dem.iterrows():
        if not linha_valida(row):
            continue
        if not competencia_de_data(row["data_rescisao"], ano, mes):
            continue
        nome = str(row["nome"]).strip()
        nrm = norm(nome)
        id_rh = dim_rh[nrm]["id_rh"] if nrm in dim_rh else None
        if not id_rh:
            nao_cadastrados.add(nome)
        setor = str(row["setor"]).strip() if str(row["setor"]) != "nan" else ""
        cargo = str(row["cargo"]).strip() if str(row["cargo"]) != "nan" else ""
        linhas_dem.append(
            f"({sql_val(id_rh)}, '{competencia}', {sql_val(nome)}, {sql_val(setor)}, "
            f"{sql_val(cargo)}, {sql_val(row.get('cbo'))}, {sql_val(row.get('data_admissao'), 'date')}, "
            f"{sql_val(row['data_rescisao'], 'date')}, {sql_val(row.get('matricula_esocial'))}, "
            f"{sql_val(row.get('cpf'))}, {sql_val(row.get('sexo'))}, 'IMPORT')"
        )

    sql_parts = [
        f"-- Importação contratações/demissões — competência {mes:02d}/{ano}",
        f"-- Fonte: {ARQ_ADMISSAO.name} + {ARQ_DEMISSAO.name}",
        "-- Rode após sql/007_rh_admissoes_demissoes.sql",
        "",
        f"delete from rh_admissoes_mensal where competencia = '{competencia}';",
        f"delete from rh_demissoes_mensal where competencia = '{competencia}';",
        "",
    ]

    if linhas_adm:
        sql_parts += [
            "insert into rh_admissoes_mensal (",
            "    id_rh, competencia, nome, setor, cargo, cbo, data_admissao,",
            "    matricula_esocial, cpf, sexo, grau_instrucao, origem",
            ") values",
            ",\n".join(linhas_adm) + ";",
            "",
        ]
    else:
        sql_parts.append("-- Nenhuma admissão nesta competência.")

    if linhas_dem:
        sql_parts += [
            "insert into rh_demissoes_mensal (",
            "    id_rh, competencia, nome, setor, cargo, cbo, data_admissao, data_rescisao,",
            "    matricula_esocial, cpf, sexo, origem",
            ") values",
            ",\n".join(linhas_dem) + ";",
            "",
        ]
    else:
        sql_parts.append("-- Nenhuma demissão nesta competência.")

    sql_parts += [
        f"select 'admissoes' as tipo, count(*) from rh_admissoes_mensal where competencia = '{competencia}'",
        f"union all select 'demissoes', count(*) from rh_demissoes_mensal where competencia = '{competencia}';",
    ]

    saida.write_text("\n".join(sql_parts), encoding="utf-8")
    print(f"OK: {len(linhas_adm)} admissões, {len(linhas_dem)} demissões -> {saida}")
    if nao_cadastrados:
        print(f"\nAVISO: {len(nao_cadastrados)} nome(s) sem id_rh em dim_rh (importados com id_rh null):")
        for n in sorted(nao_cadastrados):
            print(f"  - {n}")


if __name__ == "__main__":
    main()
