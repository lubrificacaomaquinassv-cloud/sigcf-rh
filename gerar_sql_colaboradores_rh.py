# -*- coding: utf-8 -*-
"""Gera SQL de colaboradores ativos a partir de planilha Excel do RH.

Colunas esperadas (detecção automática):
  - Nome / Colaborador / Funcionário
  - Setor / Função / Cargo (opcional — default ADMINISTRATIVO)
  - Matrícula / ID (opcional — gera RH-001, RH-002…)

Saída: sql/colaboradores_rh_gerado.sql → cole no Supabase.
"""
from pathlib import Path
import sys

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "sql" / "colaboradores_rh_gerado.sql"

# Ajuste o caminho da planilha do RH:
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
        print("Colunas: Nome | Setor (opcional) | Matricula (opcional)")
        sys.exit(1)

    df = pd.read_excel(ARQUIVO)
    cols = list(df.columns)
    col_nome = achar_coluna(cols, ["NOME", "COLABOR", "FUNCION"])
    col_setor = achar_coluna(cols, ["SETOR", "FUNCAO", "CARGO", "AREA"])
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
        funcao = str(row[col_setor]).strip().upper() if col_setor and str(row[col_setor]) != "nan" else "ADMINISTRATIVO"
        if col_id and str(row[col_id]) != "nan":
            cid = str(row[col_id]).strip().upper().replace(" ", "-")
        else:
            cid = f"RH-{seq:04d}"
            seq += 1
        nome_sql = nome.replace("'", "''")
        linhas.append(f"('{cid}', '{nome_sql}', '{funcao}', 0, true)")

    if not linhas:
        sys.exit("Nenhuma linha válida na planilha.")

    sql = (
        "-- Gerado automaticamente — gerar_sql_colaboradores_rh.py\n"
        "insert into dim_colaborador (id_colaborador, nome, funcao, custo_hora, ativo) values\n"
        + ",\n".join(linhas)
        + "\non conflict (id_colaborador) do update set\n"
        "    nome = excluded.nome,\n"
        "    funcao = excluded.funcao,\n"
        "    ativo = excluded.ativo;\n"
    )
    SAIDA.write_text(sql, encoding="utf-8")
    print(f"OK: {len(linhas)} colaboradores → {SAIDA}")


if __name__ == "__main__":
    main()
