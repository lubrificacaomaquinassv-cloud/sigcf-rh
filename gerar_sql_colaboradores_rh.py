# -*- coding: utf-8 -*-
"""Gera SQL de funcionários para dim_rh a partir de planilha Excel do RH.

Colunas esperadas (detecção automática):
  - Nome / Colaborador / Funcionário
  - Setor / Área (opcional)
  - Cargo / Função (opcional)
  - Matrícula / ID (opcional — gera RH-0001, RH-0002…)

Uso:
  python gerar_sql_colaboradores_rh.py
  python gerar_sql_colaboradores_rh.py "C:\\caminho\\Colaboradores_Ativos.xls"

Saída: sql/dim_rh_gerado.sql → cole no Supabase.
"""
from pathlib import Path
import sys
import unicodedata

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "sql" / "dim_rh_gerado.sql"
ARQUIVO_PADRAO = PASTA / "colaboradores_rh.xlsx"


def norm(s):
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.strip().upper()


def achar_coluna(cols, candidatos):
    for c in cols:
        n = norm(c)
        if any(t in n for t in candidatos):
            return c
    return None


def esc_sql(val: str) -> str:
    return val.replace("'", "''")


def main():
    try:
        import pandas as pd
    except ImportError:
        print("Instale: pip install pandas openpyxl xlrd")
        sys.exit(1)

    arquivo = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else ARQUIVO_PADRAO
    if not arquivo.is_file():
        print(f"Arquivo não encontrado: {arquivo}")
        print("Uso: python gerar_sql_colaboradores_rh.py [caminho_planilha.xls]")
        sys.exit(1)

    df = pd.read_excel(arquivo)
    cols = list(df.columns)
    col_nome = achar_coluna(cols, ["NOME", "COLABOR", "FUNCION"])
    col_setor = achar_coluna(cols, ["SETOR", "AREA", "DEPART"])
    col_cargo = achar_coluna(cols, ["CARGO", "FUNCAO", "FUNÇÃO", "CARG"])
    col_id = achar_coluna(cols, ["MATRIC", "COD"])

    if not col_nome:
        print("Colunas encontradas:", cols)
        sys.exit("Não achei coluna de NOME.")

    linhas = []
    seq = 1
    for _, row in df.iterrows():
        nome = str(row[col_nome]).strip()
        if not nome or nome.lower() == "nan":
            continue
        nome_norm = norm(nome)
        if any(x in nome_norm for x in ("TOTAL", "REGISTRO", "SOMA", "SUBTOTAL")):
            continue
        setor = str(row[col_setor]).strip() if col_setor and str(row[col_setor]) != "nan" else "Outros"
        cargo = str(row[col_cargo]).strip() if col_cargo and str(row[col_cargo]) != "nan" else None
        if col_id and str(row[col_id]) != "nan":
            cid = str(row[col_id]).strip().upper().replace(" ", "-")
        else:
            cid = f"RH-{seq:04d}"
            seq += 1
        cargo_sql = "null" if not cargo else f"'{esc_sql(cargo)}'"
        linhas.append(f"('{cid}', '{esc_sql(nome)}', '{esc_sql(setor)}', {cargo_sql}, true)")

    if not linhas:
        sys.exit("Nenhuma linha válida na planilha.")

    sql = (
        f"-- Gerado de: {arquivo.name} ({len(linhas)} funcionários)\n"
        "-- Rode após sql/002_dim_rh.sql\n"
        "insert into dim_rh (id_rh, nome, setor, cargo, ativo) values\n"
        + ",\n".join(linhas)
        + "\non conflict (id_rh) do update set\n"
        "    nome = excluded.nome,\n"
        "    setor = excluded.setor,\n"
        "    cargo = excluded.cargo,\n"
        "    ativo = excluded.ativo;\n"
        "\nselect setor, count(*) as qtd from dim_rh where ativo group by setor order by setor;\n"
    )
    SAIDA.write_text(sql, encoding="utf-8")
    print(f"OK: {len(linhas)} funcionarios -> {SAIDA}")


if __name__ == "__main__":
    main()
