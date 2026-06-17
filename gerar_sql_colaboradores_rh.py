# -*- coding: utf-8 -*-
"""Gera SQL de funcionários para dim_rh a partir de planilha Excel do RH.

Colunas esperadas (detecção automática):
  - Nome / Colaborador / Funcionário
  - Setor / Área (opcional)
  - Cargo / Função (opcional)
  - Matrícula / ID (opcional — gera RH-0001, RH-0002…)

Saída: sql/dim_rh_gerado.sql → cole no Supabase.
"""
from pathlib import Path
import sys

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "sql" / "dim_rh_gerado.sql"
ARQUIVO = PASTA / "colaboradores_rh.xlsx"


def norm(s):
    return str(s).strip().upper()


def achar_coluna(cols, candidatos):
    for c in cols:
        n = norm(c)
        if any(t in n for t in candidatos):
            return c
    return None


def main():
    try:
        import pandas as pd
    except ImportError:
        print("Instale: pip install pandas openpyxl")
        sys.exit(1)

    if not ARQUIVO.is_file():
        print(f"Coloque a planilha em: {ARQUIVO}")
        print("Colunas: Nome | Setor | Cargo | Matricula (opcionais)")
        sys.exit(1)

    df = pd.read_excel(ARQUIVO)
    cols = list(df.columns)
    col_nome = achar_coluna(cols, ["NOME", "COLABOR", "FUNCION"])
    col_setor = achar_coluna(cols, ["SETOR", "AREA", "DEPART"])
    col_cargo = achar_coluna(cols, ["CARGO", "FUNCAO", "FUNÇÃO", "CARG"])
    col_id = achar_coluna(cols, ["MATRIC", "ID", "COD"])

    if not col_nome:
        print("Colunas encontradas:", cols)
        sys.exit("Não achei coluna de NOME.")

    linhas = []
    seq = 1
    for _, row in df.iterrows():
        nome = str(row[col_nome]).strip()
        if not nome or nome.lower() == "nan":
            continue
        setor = str(row[col_setor]).strip() if col_setor and str(row[col_setor]) != "nan" else "Outros"
        cargo = str(row[col_cargo]).strip() if col_cargo and str(row[col_cargo]) != "nan" else None
        if col_id and str(row[col_id]) != "nan":
            cid = str(row[col_id]).strip().upper().replace(" ", "-")
        else:
            cid = f"RH-{seq:04d}"
            seq += 1
        nome_sql = nome.replace("'", "''")
        setor_sql = setor.replace("'", "''")
        cargo_sql = "null" if not cargo else f"'{cargo.replace(chr(39), chr(39)*2)}'"
        linhas.append(f"('{cid}', '{nome_sql}', '{setor_sql}', {cargo_sql}, true)")

    if not linhas:
        sys.exit("Nenhuma linha válida na planilha.")

    sql = (
        "-- Gerado automaticamente — gerar_sql_colaboradores_rh.py\n"
        "insert into dim_rh (id_rh, nome, setor, cargo, ativo) values\n"
        + ",\n".join(linhas)
        + "\non conflict (id_rh) do update set\n"
        "    nome = excluded.nome,\n"
        "    setor = excluded.setor,\n"
        "    cargo = excluded.cargo,\n"
        "    ativo = excluded.ativo;\n"
    )
    SAIDA.write_text(sql, encoding="utf-8")
    print(f"OK: {len(linhas)} funcionários → {SAIDA}")


if __name__ == "__main__":
    main()
