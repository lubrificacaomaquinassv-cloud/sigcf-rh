# -*- coding: utf-8 -*-
"""Extrai dados de Termos de Quitação (PDF) e gera SQL de UPDATE em rh_demissoes_mensal.

Processa todos os PDFs de uma pasta local — não precisa enviar arquivos pela internet.

Uso rápido (duplo clique):
  importar_rescisoes.bat

Linha de comando:
  python gerar_sql_rescisoes_pdf.py
  python gerar_sql_rescisoes_pdf.py "C:\\Users\\hmauricio\\Desktop\\RH"

PDFs escaneados (sem texto): preencha rescisoes_manual.csv e rode de novo.

Saída:
  sql/010_update_rescisoes_pdf.sql
  sql/010_rescisoes_relatorio.txt
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

import pdfplumber

PASTA = Path(__file__).resolve().parent
SAIDA = PASTA / "sql" / "010_update_rescisoes_pdf.sql"
RELATORIO = PASTA / "sql" / "010_rescisoes_relatorio.txt"
PASTA_PDF_PADRAO = Path(r"c:\Users\hmauricio\Desktop\RH")
CSV_MANUAL = PASTA / "rescisoes_manual.csv"


def norm(s) -> str:
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().upper()


def esc(v: str) -> str:
    return str(v).replace("'", "''")


def normalizar_texto_pdf(texto: str) -> str:
    t = texto.replace("\r\n", "\n")
    t = re.sub(r"\(cid:\d+\)", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    return t


def parse_moeda(texto: str) -> float | None:
    def _to_float(bruto: str) -> float | None:
        bruto = re.sub(r"\(cid:\d+\)", "", bruto).replace(" ", "").strip("., ")
        if not bruto:
            return None
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
        try:
            return round(float(bruto), 2)
        except ValueError:
            return None

    m = re.search(r"valor\s+l.quido\s+de\s+R\$?\s*(.+?)\s*,\s*o\s+qual", texto, re.I | re.S)
    if m:
        v = _to_float(m.group(1))
        if v is not None:
            return v
    m = re.search(r"valor\s+l.quido\s+de\s+R\$\s*([\d\s.,]+)", texto, re.I)
    if m:
        return _to_float(m.group(1))
    m = re.search(r"valor\s+l.quido\s+de\s+R\s*(.+?)\s*,\s*o\s+qual", texto, re.I | re.S)
    if m:
        return _to_float(m.group(1))
    return None


def extrair_campo(texto: str, rotulo: str) -> str | None:
    if rotulo == "cpf":
        m = re.search(r"(\d{3}\.\d{3}\.\d{3}-\d{2})", texto)
        return m.group(1) if m else None
    if rotulo == "nome":
        m = re.search(r"11 Nome\s*\n?\s*(.+)", texto)
        if not m:
            return None
        linha = m.group(1).strip()
        m_mat = re.search(r"\d+\s*-\s*(.+)$", linha)
        return (m_mat.group(1) if m_mat else linha).strip()
    if rotulo == "causa":
        m = re.search(r"22 Causa do Afastamento\s*\n?\s*(.+?)(?=\n?\s*24 Data)", texto, re.S)
        return m.group(1).strip() if m else None
    if rotulo in ("data_adm", "data_aviso", "data_resc", "codigo"):
        m = re.search(
            r"(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\w+)",
            texto,
        )
        if not m:
            return None
        mapa = {
            "data_adm": m.group(1),
            "data_aviso": m.group(2),
            "data_resc": m.group(3),
            "codigo": m.group(4),
        }
        return mapa[rotulo]
    return None


def to_sql_date(d: str | None) -> str:
    if not d or d == "00/00/0000":
        return "null"
    if re.match(r"\d{4}-\d{2}-\d{2}", str(d)):
        return f"'{d}'"
    p = str(d).split("/")
    if len(p) == 3:
        return f"'{p[2]}-{p[1]}-{p[0]}'"
    return "null"


def parse_pdf(caminho: Path) -> dict | None:
    with pdfplumber.open(caminho) as pdf:
        texto = normalizar_texto_pdf("\n".join(p.extract_text() or "" for p in pdf.pages))
    if len(texto.strip()) < 100:
        return {"arquivo": caminho.name, "_erro": "PDF escaneado (imagem) — preencha rescisoes_manual.csv"}
    if "TERMO DE QUITA" not in norm(texto) and "RESCIS" not in norm(texto):
        return None

    nome = extrair_campo(texto, "nome")
    cpf = extrair_campo(texto, "cpf")
    causa = extrair_campo(texto, "causa")
    codigo = extrair_campo(texto, "codigo")
    data_adm = extrair_campo(texto, "data_adm")
    data_aviso = extrair_campo(texto, "data_aviso")
    data_resc = extrair_campo(texto, "data_resc")
    valor_liq = parse_moeda(texto)

    if not nome and not cpf:
        return {"arquivo": caminho.name, "_erro": "Não foi possível ler nome/CPF do PDF"}

    return {
        "arquivo": caminho.name,
        "nome": nome,
        "cpf": cpf,
        "causa_rescisao": causa,
        "codigo_afastamento": codigo,
        "data_admissao": to_sql_date(data_adm),
        "data_aviso_previo": to_sql_date(data_aviso),
        "data_rescisao": to_sql_date(data_resc),
        "valor_liquido_rescisao": valor_liq,
    }


def carregar_manual() -> list[dict]:
    if not CSV_MANUAL.is_file():
        return []
    linhas = []
    with CSV_MANUAL.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            if not any(str(row.get(k) or "").strip() for k in row):
                continue
            valor = str(row.get("valor_liquido") or "").strip().replace(".", "").replace(",", ".")
            linhas.append({
                "arquivo": "rescisoes_manual.csv",
                "nome": row.get("nome", "").strip(),
                "cpf": row.get("cpf", "").strip(),
                "causa_rescisao": row.get("causa_rescisao", "").strip() or None,
                "codigo_afastamento": row.get("codigo_afastamento", "").strip() or None,
                "data_admissao": "null",
                "data_aviso_previo": "null",
                "data_rescisao": to_sql_date(row.get("data_rescisao", "").strip()),
                "valor_liquido_rescisao": float(valor) if valor else None,
            })
    return [r for r in linhas if r.get("valor_liquido_rescisao") or r.get("causa_rescisao")]


def gerar_update(d: dict) -> str | None:
    if d.get("_erro"):
        return None
    sets = []
    if d.get("causa_rescisao"):
        sets.append(f"causa_rescisao = '{esc(d['causa_rescisao'])}'")
    if d.get("codigo_afastamento"):
        sets.append(f"codigo_afastamento = '{esc(d['codigo_afastamento'])}'")
    if d.get("data_aviso_previo") and d["data_aviso_previo"] != "null":
        sets.append(f"data_aviso_previo = {d['data_aviso_previo']}")
    if d.get("valor_liquido_rescisao") is not None:
        sets.append(f"valor_liquido_rescisao = {d['valor_liquido_rescisao']:.2f}")

    if not sets:
        return None

    where_parts = []
    if d.get("cpf"):
        where_parts.append(f"cpf = '{esc(d['cpf'])}'")
    if d.get("data_rescisao") and d["data_rescisao"] != "null":
        where_parts.append(f"data_rescisao = {d['data_rescisao']}")
    if not where_parts and d.get("nome"):
        where_parts.append(f"upper(nome) = '{esc(norm(d['nome']))}'")

    return (
        f"-- {d['arquivo']} | {d.get('nome') or '?'} | "
        f"liquido R$ {d.get('valor_liquido_rescisao') or '?'}\n"
        f"update rh_demissoes_mensal set\n    "
        + ",\n    ".join(sets)
        + f"\nwhere {' and '.join(where_parts)};"
    )


def listar_pdfs(pasta: Path) -> list[Path]:
    if pasta.is_file():
        return [pasta]
    return sorted(set(pasta.glob("*.pdf")) | set(pasta.glob("*.PDF")))


def main():
    alvo = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else PASTA_PDF_PADRAO
    pdfs = listar_pdfs(alvo)
    if not pdfs and not CSV_MANUAL.is_file():
        sys.exit(f"Nenhum PDF em: {alvo}")

    linhas_sql = [
        "-- Atualização de rescisões — gerado automaticamente dos PDFs locais",
        "-- Rode após sql/009_rh_demissoes_rescisao_cols.sql",
        "",
    ]
    relatorio = [
        "RELATÓRIO — Importação Termos de Quitação",
        f"Pasta: {alvo}",
        "",
    ]
    ok = 0
    erros = []

    for pdf in pdfs:
        dados = parse_pdf(pdf)
        if dados is None:
            relatorio.append(f"IGNORADO: {pdf.name} (não é termo de quitação)")
            continue
        if dados.get("_erro"):
            relatorio.append(f"PENDENTE: {pdf.name} — {dados['_erro']}")
            erros.append(dados)
            continue
        sql = gerar_update(dados)
        if not sql:
            relatorio.append(f"AVISO: {pdf.name} — {dados.get('nome')} sem valor/campos")
            continue
        linhas_sql.append(sql)
        linhas_sql.append("")
        ok += 1
        relatorio.append(
            f"OK: {pdf.name} | {dados.get('nome')} | R$ {dados.get('valor_liquido_rescisao')}"
        )
        print(f"OK: {pdf.name} -> {dados.get('nome')} | R$ {dados.get('valor_liquido_rescisao')}")

    for dados in carregar_manual():
        sql = gerar_update(dados)
        if sql:
            linhas_sql.append(sql)
            linhas_sql.append("")
            ok += 1
            relatorio.append(
                f"OK (manual): {dados.get('nome')} | R$ {dados.get('valor_liquido_rescisao')}"
            )
            print(f"OK (manual): {dados.get('nome')} | R$ {dados.get('valor_liquido_rescisao')}")

    if erros:
        relatorio += ["", "PDFs ESCANEADOS — preencha rescisoes_manual.csv com valor e motivo:", ""]
        for e in erros:
            relatorio.append(f"  - {e['arquivo']}")

    relatorio += [
        "",
        f"Total importado: {ok}",
        "",
        "Próximo passo: cole sql/010_update_rescisoes_pdf.sql no Supabase SQL Editor.",
    ]

    if ok == 0:
        sys.exit("Nenhum registro gerado. Veja sql/010_rescisoes_relatorio.txt")

    linhas_sql.append(
        "select nome, data_rescisao, valor_liquido_rescisao, causa_rescisao "
        "from rh_demissoes_mensal where competencia = '2026-06-01' order by nome;"
    )
    SAIDA.write_text("\n".join(linhas_sql), encoding="utf-8")
    RELATORIO.write_text("\n".join(relatorio), encoding="utf-8")
    print(f"\n{ok} registro(s) -> {SAIDA}")
    print(f"Relatorio -> {RELATORIO}")


if __name__ == "__main__":
    main()
