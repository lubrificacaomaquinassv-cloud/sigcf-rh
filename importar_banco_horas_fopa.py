# -*- coding: utf-8 -*-
"""
Importa PDFs FOPA (Banco de Horas, Cartão Ponto, Centro de Custo) para Supabase SIGRH.

Arquivos esperados em C:\\Users\\hmauricio\\Desktop\\RH\\BANCO_HORAS:
  - Extrato Banco de Horas_2105_*.PDF  (competência Jun/2026 — ciclo 21/05–20/06)
  - Extrato Banco de Horas_2106_*.PDF  (competência Jul/2026 — ciclo 21/06–20/07)
  - Cartão Ponto_2106_*.PDF            (detalhe diário Jun–Jul)
  - Centro de Custo_072026.pdf         (folha analítica Jul/2026)

Uso:
  python importar_banco_horas_fopa.py
  python importar_banco_horas_fopa.py --pasta "C:\\Users\\hmauricio\\Desktop\\RH\\BANCO_HORAS"
  python importar_banco_horas_fopa.py --dry-run
  python importar_banco_horas_fopa.py --sql-only   # gera sql/import_banco_horas_gerado.sql

Pré-requisito Supabase (rodar uma vez):
  sql/003_rh_banco_horas_folha_ponto.sql
  sql/004_rh_ponto_dia_e_views.sql
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from rh_fopa_norm import (
    extract_times,
    normalizar_setor,
    norm,
    parse_br_money,
    parse_he_linha,
    parse_hhmm_to_decimal,
    tipo_ponto_para_app,
)

PASTA_PADRAO = Path(r"C:\Users\hmauricio\Desktop\RH\BANCO_HORAS")
ROOT = Path(__file__).resolve().parent
SECRETS = ROOT.parent / "requisicao-compras" / ".streamlit" / "secrets.toml"
SQL_SAIDA = ROOT / "sql" / "import_banco_horas_gerado.sql"

# Viagem coletiva exame periódico — 10/07/2026
DATA_EXAME_PERIODICO = date(2026, 7, 10)

DATE_BR_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
PERIOD_RE = re.compile(
    r"DE\s+(\d{2}/\d{2}/\d{4})\s+AT[EÉ]\s+(\d{2}/\d{2}/\d{4})",
    re.I,
)
TOTAL_SETOR_RE = re.compile(
    r"^TOTAL\s+(.+?):\s+(\d+)\s+FUNCION",
    re.I,
)
CC_RE = re.compile(r"C\.Custo:(\S+)\s+(.+)", re.I)
EMITIDO_RE = re.compile(r"Emitido em (\d{2}/\d{2}/\d{4})", re.I)


def esc(val) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float, Decimal)):
        return str(val)
    return "'" + str(val).replace("'", "''") + "'"


def parse_date_br(s: str) -> date | None:
    m = DATE_BR_RE.search(s)
    if not m:
        return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_br_number(s: str) -> float:
    return parse_br_money(s)


def competencia_from_period_end(end: date) -> date:
    """Ciclo FOPA 21→20: fim 20/06 → competência 2026-06-01."""
    return date(end.year, end.month, 1)


def read_pdf_text(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise SystemExit("Instale: pip install pdfplumber")
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts)


@dataclass
class BancoHorasRow:
    id_rh: str
    nome: str
    cargo: str
    setor: str
    competencia: date
    horas_he_100: float = 0.0
    horas_credito: float = 0.0
    horas_debito: float = 0.0
    saldo_mes: float = 0.0
    saldo_acumulado: float = 0.0
    horas_he_50: float = 0.0


@dataclass
class BancoSetorRow:
    setor: str
    competencia: date
    qtd_colaboradores: int
    horas_saldo_total: float
    horas_he_50: float = 0.0
    horas_he_100: float = 0.0


@dataclass
class PontoDiaRow:
    id_rh: str
    nome: str
    setor: str
    cargo: str
    data: date
    competencia: date
    tipo_dia: str
    horas_abonadas: float = 0.0
    horas_debito: float = 0.0
    possui_atestado: bool = False
    observacao: str = ""


@dataclass
class JustificativaRow:
    data_falta: date
    id_rh: str
    nome_colaborador: str
    setor: str
    funcao: str
    tipo_justificativa: str
    dias_ausencia: float
    possui_atestado: bool
    motivo: str


@dataclass
class FolhaSetorRow:
    competencia: date
    codigo_cc: str
    setor: str
    qtd_colaboradores: int
    total_proventos: float
    total_descontos: float
    total_liquido: float
    total_folha: float
    horas_he_50: float
    valor_he_50: float
    horas_he_100: float
    valor_he_100: float


@dataclass
class ImportBundle:
    banco_horas: list[BancoHorasRow] = field(default_factory=list)
    banco_setor: list[BancoSetorRow] = field(default_factory=list)
    ponto_dia: list[PontoDiaRow] = field(default_factory=list)
    ponto_mensal: list[dict] = field(default_factory=list)
    justificativas: list[JustificativaRow] = field(default_factory=list)
    folha_setor: list[FolhaSetorRow] = field(default_factory=list)
    ponto_tipos: list[dict] = field(default_factory=list)


def parse_banco_horas_pdf(path: Path) -> tuple[list[BancoHorasRow], list[BancoSetorRow]]:
    text = read_pdf_text(path)
    pm = PERIOD_RE.search(text)
    if not pm:
        raise ValueError(f"Período não encontrado em {path.name}")
    end = parse_date_br(pm.group(2))
    comp = competencia_from_period_end(end)

    rows: list[BancoHorasRow] = []
    setores: list[BancoSetorRow] = []
    setor_atual = "Outros"

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("Emitido") or "NOME DO FUNCION" in line:
            continue
        tm = TOTAL_SETOR_RE.match(line)
        if tm:
            raw_setor = tm.group(1).strip()
            if norm(raw_setor) in ("GERAL", ""):
                setor_atual = raw_setor
                continue
            setor_atual = normalizar_setor(raw_setor) or raw_setor
            _, times = extract_times(line)
            if len(times) >= 1:
                setores.append(
                    BancoSetorRow(
                        setor=setor_atual,
                        competencia=comp,
                        qtd_colaboradores=int(tm.group(2)),
                        horas_saldo_total=parse_hhmm_to_decimal(times[-1]),
                        horas_he_100=parse_hhmm_to_decimal(times[0]) if times else 0,
                    )
                )
            continue
        if line.startswith("TOTAL ") or "FUNCIONÁRIOS" in line.upper():
            continue
        _, times = extract_times(line)
        if not times:
            continue
        rest, _ = extract_times(line)
        m_mat = re.search(r"\s(\d{1,5})\s", rest)
        if not m_mat:
            continue
        mat = m_mat.group(1)
        nome = rest[: m_mat.start()].strip()
        meio = rest[m_mat.end():].strip()
        if not nome or len(nome) < 4:
            continue
        # últimas palavras em maiúsculo = departamento
        tokens = meio.split()
        dept_tokens = []
        cargo_tokens = []
        for tok in reversed(tokens):
            if tok.isupper() or "/" in tok or tok in ("DE", "DO", "DA", "NA", "E", "II", "I"):
                dept_tokens.insert(0, tok)
            else:
                cargo_tokens = tokens[: len(tokens) - len(dept_tokens)]
                break
        if not dept_tokens:
            cargo_tokens = tokens[:-1] if len(tokens) > 1 else tokens
            dept_tokens = [setor_atual]
        cargo = " ".join(cargo_tokens) if cargo_tokens else meio
        dept = normalizar_setor(setor_atual) or setor_atual

        saldo_acum = parse_hhmm_to_decimal(times[-1])
        saldo_mes = parse_hhmm_to_decimal(times[-2]) if len(times) >= 2 else saldo_acum
        credito = parse_hhmm_to_decimal(times[-3]) if len(times) >= 3 else 0
        debito = parse_hhmm_to_decimal(times[-4]) if len(times) >= 4 else 0
        he100 = parse_hhmm_to_decimal(times[0]) if times else 0

        if not is_colaborador_valido(mat, nome):
            continue
        rows.append(
            BancoHorasRow(
                id_rh=mat,
                nome=nome,
                cargo=cargo,
                setor=dept,
                competencia=comp,
                horas_he_100=he100,
                horas_credito=max(credito, 0),
                horas_debito=abs(debito) if debito < 0 else debito,
                saldo_mes=saldo_mes,
                saldo_acumulado=saldo_acum,
            )
        )
    return rows, setores


def classify_ponto_tipo(dia: date, texto: str) -> tuple[str, bool]:
    t = norm(texto)
    possui_atestado = "ATESTADO" in t

    if dia == DATA_EXAME_PERIODICO:
        if any(x in t for x in ("SERVICO EXTERNO", "DISPENSA PONTO", "ABONAR")):
            return "EXAME PERIODICO", possui_atestado
        if "ATESTADO" in t:
            return "EXAME PERIODICO", True

    if "FERIAS" in t or "FÉRIAS" in texto:
        return "FERIAS", False
    if "AFASTAMENTO" in t:
        return "AFASTAMENTO", False
    if "ATESTADO" in t:
        return "ATESTADO MEDICO", True
    if "FALTA" in t and "FOLGA" not in t:
        return "FALTA", False
    if "FOLGA" in t:
        return "FOLGA", False
    if "BANCO" in t and "SALDO" not in t:
        return "BANCO", False
    if "DISPENSA" in t:
        return "DISPENSA", False
    if "ABONAR" in t or "SERVICO EXTERNO" in t:
        return "ABONO", False
    return "NORMAL", False


def tipo_para_justificativa(tipo_dia: str) -> str | None:
    m = {
        "FALTA": "Falta injustificada",
        "FERIAS": "Férias",
        "AFASTAMENTO": "Afastamento INSS",
        "ATESTADO MEDICO": "Atestado médico",
        "EXAME PERIODICO": "Exame periódico",
        "DISPENSA": "Dispensa",
        "ABONO": "Abono",
    }
    return m.get(tipo_dia)


def parse_ponto_pdf(path: Path) -> tuple[list[PontoDiaRow], list[dict], list[JustificativaRow]]:
    try:
        import pdfplumber
    except ImportError:
        raise SystemExit("Instale: pip install pdfplumber")

    ponto_dia: list[PontoDiaRow] = []
    ponto_mensal: list[dict] = []
    justificativas: list[JustificativaRow] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pm = PERIOD_RE.search(text)
            if not pm:
                continue
            end = parse_date_br(pm.group(2))
            comp = competencia_from_period_end(end)

            nome_m = re.search(
                r"NOME DO FUNCION[^\n]+:\s*(.+?)\s+N[^\n]*MATR[^\n]+:\s*(\d+)",
                text,
                re.I,
            )
            if not nome_m:
                continue
            nome = nome_m.group(1).strip()
            mat = nome_m.group(2).strip()
            if not is_colaborador_valido(mat, nome):
                continue
            cargo_m = re.search(r"NOME DO CARGO:\s*(.+?)\s+NOME DO DEPARTAMENTO:", text, re.I)
            dept_m = re.search(r"NOME DO DEPARTAMENTO:\s*(.+?)\s+ENT\.", text, re.I)
            cargo = cargo_m.group(1).strip() if cargo_m else ""
            setor = normalizar_setor(dept_m.group(1).strip() if dept_m else "Outros") or "Outros"

            dias_falta = dias_ferias = dias_atraso = 0.0
            horas_cred = horas_deb = 0.0

            for line in text.splitlines():
                dm = DATE_BR_RE.match(line.strip())
                if not dm:
                    continue
                dia = parse_date_br(dm.group(0))
                if not dia:
                    continue
                resto = line[dm.end():].strip()
                tipo, possui_atestado = classify_ponto_tipo(dia, resto)
                _, times = extract_times(resto)
                h_abon = 0.0
                h_deb = 0.0
                for t in times:
                    v = parse_hhmm_to_decimal(t)
                    if v > 0 and h_abon == 0 and tipo in ("ABONO", "EXAME PERIODICO", "BANCO"):
                        h_abon = v
                    elif v < 0:
                        h_deb = abs(v)

                if tipo != "NORMAL":
                    ponto_dia.append(
                        PontoDiaRow(
                            id_rh=mat,
                            nome=nome,
                            setor=setor,
                            cargo=cargo,
                            data=dia,
                            competencia=comp,
                            tipo_dia=tipo,
                            horas_abonadas=h_abon,
                            horas_debito=h_deb,
                            possui_atestado=possui_atestado,
                            observacao=resto[:200],
                        )
                    )
                    jt = tipo_para_justificativa(tipo)
                    if jt:
                        justificativas.append(
                            JustificativaRow(
                                data_falta=dia,
                                id_rh=mat,
                                nome_colaborador=nome,
                                setor=setor,
                                funcao=cargo,
                                tipo_justificativa=jt,
                                dias_ausencia=1.0,
                                possui_atestado=possui_atestado,
                                motivo=resto[:250],
                            )
                        )

                if tipo == "FALTA":
                    dias_falta += 1
                elif tipo == "FERIAS":
                    dias_ferias += 1
                if h_deb > 0:
                    dias_atraso += 0.5
                horas_cred += max(h_abon, 0)
                horas_deb += h_deb

            tot_m = re.search(r"TOTAIS\s+(-?\d{1,4}:\d{2})\s+(-?\d{1,4}:\d{2})", text)
            saldo_final = 0.0
            if tot_m:
                horas_cred = parse_hhmm_to_decimal(tot_m.group(2))
                saldo_final = parse_hhmm_to_decimal(tot_m.group(2))

            ponto_mensal.append(
                {
                    "id_rh": mat,
                    "competencia": comp,
                    "nome_colaborador": nome,
                    "setor": setor,
                    "dias_falta": dias_falta,
                    "dias_atraso": dias_atraso,
                    "faltas_injustificadas": dias_falta,
                    "horas_realizadas": horas_cred,
                    "observacao": f"Import {path.name}",
                }
            )

    return ponto_dia, ponto_mensal, justificativas


def parse_centro_custo_pdf(path: Path) -> list[FolhaSetorRow]:
    text = read_pdf_text(path)
    comp = date(2026, 7, 1)
    em = re.search(r"Per[ií]odo:\s*(\d{2}/\d{2}/\d{4})", text, re.I)
    if em:
        d = parse_date_br(em.group(1))
        if d:
            comp = date(d.year, d.month, 1)

    rows: list[FolhaSetorRow] = []
    blocks = re.split(r"(?=C\.Custo:)", text)
    for block in blocks:
        cm = CC_RE.search(block)
        if not cm:
            continue
        codigo = cm.group(1).strip()
        setor_raw = cm.group(2).strip().split("\n")[0].strip()
        setor = normalizar_setor(setor_raw)
        if not setor:
            continue

        he50_h = he100_h = val50 = val100 = 0.0
        for line in block.splitlines():
            ls = line.strip()
            if ls.startswith("257 "):
                he50_h, val50 = parse_he_linha(ls, "257")
            if ls.startswith("259 "):
                he100_h, val100 = parse_he_linha(ls, "259")

        prov = desc = liq = tot_folha = 0.0
        qtd = 0
        for line in block.splitlines():
            if line.startswith("Proventos:"):
                nums = re.findall(r"[\d.,]+", line)
                if nums:
                    prov = parse_br_number(nums[0])
            if line.startswith("Descontos:"):
                nums = re.findall(r"[\d.,]+", line)
                if nums:
                    desc = parse_br_number(nums[0])
            if line.startswith("Líquido:") or line.startswith("Liquido:"):
                nums = re.findall(r"[\d.,]+", line)
                if nums:
                    liq = parse_br_number(nums[0])
            if "Total da Folha:" in line:
                nums = re.findall(r"[\d.,]+", line)
                if nums:
                    tot_folha = parse_br_number(nums[-1])
            if "Total de Colaboradores" in line:
                m = re.search(r"(\d+)\s*$", line.strip())
                if m:
                    qtd = int(m.group(1))

        rows.append(
            FolhaSetorRow(
                competencia=comp,
                codigo_cc=codigo,
                setor=setor,
                qtd_colaboradores=qtd,
                total_proventos=prov,
                total_descontos=desc,
                total_liquido=liq,
                total_folha=tot_folha,
                horas_he_50=he50_h,
                valor_he_50=val50,
                horas_he_100=he100_h,
                valor_he_100=val100,
            )
        )

        # Enriquecer rh_banco_horas_setor com valores HE quando existir match
    return rows


def is_colaborador_valido(id_rh: str, nome: str) -> bool:
    if not id_rh or id_rh == "0":
        return False
    n = norm(nome)
    if n in ("ADMINISTRADOR", "TOTAL", ""):
        return False
    return True


def merge_banco_setor(setores: list[BancoSetorRow]) -> list[BancoSetorRow]:
    """Unifica setores duplicados (variantes de maiúscula/acento)."""
    merged: dict[tuple[date, str], BancoSetorRow] = {}
    for s in setores:
        ns = normalizar_setor(s.setor) or s.setor
        if norm(ns) in ("GERAL", ""):
            continue
        key = (s.competencia, ns)
        if key not in merged:
            merged[key] = BancoSetorRow(
                setor=ns,
                competencia=s.competencia,
                qtd_colaboradores=s.qtd_colaboradores,
                horas_saldo_total=s.horas_saldo_total,
                horas_he_50=s.horas_he_50,
                horas_he_100=s.horas_he_100,
            )
        else:
            cur = merged[key]
            if s.qtd_colaboradores > cur.qtd_colaboradores:
                cur.qtd_colaboradores = s.qtd_colaboradores
            if abs(s.horas_saldo_total) > abs(cur.horas_saldo_total):
                cur.horas_saldo_total = s.horas_saldo_total
            cur.horas_he_50 = max(cur.horas_he_50, s.horas_he_50)
            cur.horas_he_100 = max(cur.horas_he_100, s.horas_he_100)
    return list(merged.values())


def build_ponto_tipos(bundle: ImportBundle) -> list[dict]:
    agg: dict[tuple[str, date, str], dict] = {}
    for p in bundle.ponto_dia:
        if p.tipo_dia in ("NORMAL", "FOLGA", "BANCO"):
            continue
        tipo, desc = tipo_ponto_para_app(p.tipo_dia)
        key = (p.id_rh, p.competencia, tipo)
        row = agg.setdefault(
            key,
            {
                "id_rh": p.id_rh,
                "competencia": p.competencia,
                "setor": p.setor,
                "tipo": tipo,
                "tipo_descricao": desc,
                "qtd_dias": 0.0,
            },
        )
        row["qtd_dias"] += 1.0
    return list(agg.values())


def sync_dim_rh(cur, bundle: ImportBundle) -> int:
    """Vincula matrícula FOPA → dim_rh (nome/setor/cargo)."""
    people: dict[str, tuple[str, str, str]] = {}
    for r in bundle.banco_horas:
        people[r.id_rh] = (r.nome, r.setor, r.cargo)
    for p in bundle.ponto_dia:
        if p.id_rh not in people:
            people[p.id_rh] = (p.nome, p.setor, p.cargo)

    cur.execute("select id_rh, matricula, nome from dim_rh")
    by_mat: dict[str, str] = {}
    by_nome: dict[str, str] = {}
    for id_rh, matricula, nome in cur.fetchall():
        if matricula:
            by_mat[str(matricula).strip()] = id_rh
        if nome:
            by_nome[norm(nome)] = id_rh

    n = 0
    for matricula, (nome, setor, cargo) in people.items():
        existing = by_mat.get(str(matricula).strip()) or by_nome.get(norm(nome))
        if existing:
            cur.execute(
                """
                update dim_rh
                set matricula = %s, nome = %s, setor = %s, cargo = %s, ativo = true
                where id_rh = %s
                """,
                (matricula, nome, setor, cargo, existing),
            )
        else:
            cur.execute(
                """
                insert into dim_rh (id_rh, matricula, nome, setor, cargo, ativo)
                values (%s, %s, %s, %s, %s, true)
                on conflict (id_rh) do update set
                    matricula = excluded.matricula,
                    nome = excluded.nome,
                    setor = excluded.setor,
                    cargo = excluded.cargo,
                    ativo = true
                """,
                (matricula, matricula, nome, setor, cargo),
            )
            by_mat[str(matricula).strip()] = matricula
        by_nome[norm(nome)] = existing or matricula
        n += 1
    return n


def limpar_dados_fopa(cur) -> None:
    """Remove importações anteriores (Jun/Jul 2026+) para evitar duplicatas."""
    cur.execute("delete from rh_banco_horas where competencia >= '2026-06-01'")
    cur.execute("delete from rh_banco_horas_setor where competencia >= '2026-06-01'")
    cur.execute(
        "delete from rh_ponto_dia where origem = 'FOPA_PDF' "
        "and competencia >= '2026-06-01'"
    )
    cur.execute(
        "delete from rh_folha_setor where origem = 'FOPA_CC' "
        "and competencia >= '2026-06-01'"
    )
    cur.execute(
        "delete from rh_ponto_mensal where competencia >= '2026-06-01' "
        "and coalesce(observacao, '') ilike '%Import%'"
    )
    cur.execute(
        "delete from rh_ponto_tipos_mensal where origem = 'IMPORT_PDF' "
        "and competencia >= '2026-06-01'"
    )


def discover_files(pasta: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {
        "banco": [],
        "ponto": [],
        "centro": [],
    }
    if not pasta.is_dir():
        raise SystemExit(f"Pasta não encontrada: {pasta}")
    for f in sorted(pasta.iterdir()):
        if not f.is_file():
            continue
        n = norm(f.name)
        if f.suffix.lower() != ".pdf":
            continue
        if "EXTRATO" in n and "BANCO" in n:
            out["banco"].append(f)
        elif "CART" in n and "PONTO" in n:
            out["ponto"].append(f)
        elif "CENTRO" in n and "CUSTO" in n:
            out["centro"].append(f)
    return out


def load_all(pasta: Path) -> ImportBundle:
    files = discover_files(pasta)
    bundle = ImportBundle()

    for bf in files["banco"]:
        print(f"  Banco de horas: {bf.name}")
        bh, bs = parse_banco_horas_pdf(bf)
        bundle.banco_horas.extend(bh)
        bundle.banco_setor.extend(bs)

    for pf in files["ponto"]:
        print(f"  Cartão ponto: {pf.name}")
        pd, pm, jf = parse_ponto_pdf(pf)
        bundle.ponto_dia.extend(pd)
        bundle.ponto_mensal.extend(pm)
        bundle.justificativas.extend(jf)

    for cf in files["centro"]:
        print(f"  Centro de custo: {cf.name}")
        bundle.folha_setor.extend(parse_centro_custo_pdf(cf))

    # Dedupe banco_horas por id_rh+competencia (último vence)
    seen = {}
    for r in bundle.banco_horas:
        seen[(r.id_rh, r.competencia)] = r
    bundle.banco_horas = list(seen.values())

    bundle.banco_setor = merge_banco_setor(bundle.banco_setor)
    bundle.ponto_tipos = build_ponto_tipos(bundle)

    return bundle


def gerar_sql(bundle: ImportBundle) -> str:
    lines = [
        "-- Gerado por importar_banco_horas_fopa.py",
        f"-- {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    for r in bundle.banco_horas:
        lines.append(
            "insert into rh_banco_horas (id_rh, competencia, setor, horas_he_50, horas_he_100, "
            "horas_credito, horas_debito, saldo_mes, saldo_acumulado, origem) values ("
            f"{esc(r.id_rh)}, {esc(r.competencia.isoformat())}, {esc(r.setor)}, "
            f"{r.horas_he_50:.2f}, {r.horas_he_100:.2f}, {r.horas_credito:.2f}, {r.horas_debito:.2f}, "
            f"{r.saldo_mes:.2f}, {r.saldo_acumulado:.2f}, 'FOPA_PDF'"
            ") on conflict (id_rh, competencia) do update set "
            "setor=excluded.setor, horas_he_50=excluded.horas_he_50, horas_he_100=excluded.horas_he_100, "
            "horas_credito=excluded.horas_credito, horas_debito=excluded.horas_debito, "
            "saldo_mes=excluded.saldo_mes, saldo_acumulado=excluded.saldo_acumulado, origem='FOPA_PDF';"
        )

    for s in bundle.banco_setor:
        lines.append(
            "insert into rh_banco_horas_setor (competencia, setor, qtd_colaboradores, horas_he_100, "
            "horas_saldo_total, origem) values ("
            f"{esc(s.competencia.isoformat())}, {esc(s.setor)}, {s.qtd_colaboradores}, "
            f"{s.horas_he_100:.2f}, {s.horas_saldo_total:.2f}, 'FOPA_PDF'"
            ") on conflict (competencia, setor) do update set "
            "qtd_colaboradores=excluded.qtd_colaboradores, horas_he_100=excluded.horas_he_100, "
            "horas_saldo_total=excluded.horas_saldo_total;"
        )

    for p in bundle.ponto_dia:
        lines.append(
            "insert into rh_ponto_dia (id_rh, data, competencia, nome_colaborador, setor, cargo, "
            "tipo_dia, horas_abonadas, horas_debito, possui_atestado, observacao, origem) values ("
            f"{esc(p.id_rh)}, {esc(p.data.isoformat())}, {esc(p.competencia.isoformat())}, "
            f"{esc(p.nome)}, {esc(p.setor)}, {esc(p.cargo)}, {esc(p.tipo_dia)}, "
            f"{p.horas_abonadas:.2f}, {p.horas_debito:.2f}, {esc(p.possui_atestado)}, "
            f"{esc(p.observacao)}, 'FOPA_PDF'"
            ") on conflict (id_rh, data, tipo_dia) do update set "
            "horas_abonadas=excluded.horas_abonadas, horas_debito=excluded.horas_debito, "
            "observacao=excluded.observacao;"
        )

    for j in bundle.justificativas:
        lines.append(
            "insert into rh_justificativa_faltas (data_falta, id_rh, nome_colaborador, setor, funcao, "
            "tipo_justificativa, dias_ausencia, possui_atestado, motivo, status) values ("
            f"{esc(j.data_falta.isoformat())}, {esc(j.id_rh)}, {esc(j.nome_colaborador)}, "
            f"{esc(j.setor)}, {esc(j.funcao)}, {esc(j.tipo_justificativa)}, {j.dias_ausencia}, "
            f"{esc(j.possui_atestado)}, {esc(j.motivo)}, 'IMPORTADO'"
            ");"
        )

    for f in bundle.folha_setor:
        lines.append(
            "insert into rh_folha_setor (competencia, codigo_cc, setor, qtd_colaboradores, "
            "total_proventos, total_descontos, total_liquido, total_folha, "
            "horas_he_50, valor_he_50, horas_he_100, valor_he_100, origem) values ("
            f"{esc(f.competencia.isoformat())}, {esc(f.codigo_cc)}, {esc(f.setor)}, {f.qtd_colaboradores}, "
            f"{f.total_proventos:.2f}, {f.total_descontos:.2f}, {f.total_liquido:.2f}, {f.total_folha:.2f}, "
            f"{f.horas_he_50:.2f}, {f.valor_he_50:.2f}, {f.horas_he_100:.2f}, {f.valor_he_100:.2f}, 'FOPA_CC'"
            ") on conflict (competencia, setor) do update set "
            "total_proventos=excluded.total_proventos, total_folha=excluded.total_folha, "
            "horas_he_50=excluded.horas_he_50, valor_he_50=excluded.valor_he_50;"
        )

    lines.extend([
        "",
        "-- Atualiza valor_total setor a partir da folha CC",
        "update rh_banco_horas_setor s set valor_total = f.valor_he_50 + f.valor_he_100",
        "from rh_folha_setor f",
        "where s.competencia = f.competencia and upper(trim(s.setor)) = upper(trim(f.setor));",
        "",
        "select * from vw_rh_banco_horas_empresa order by competencia desc;",
        "select * from vw_rh_banco_horas_setor_rank where mes_key >= '2026-06' limit 20;",
    ])
    return "\n".join(lines)


def _load_db_password() -> str:
    if not SECRETS.exists():
        raise SystemExit(f"Secrets não encontrado: {SECRETS}")
    text = SECRETS.read_text(encoding="utf-8")
    m = re.search(r'password\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("password não encontrado nos secrets")
    return m.group(1)


def aplicar_supabase(bundle: ImportBundle) -> None:
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
    except ImportError:
        raise SystemExit("Instale: pip install psycopg2-binary")

    pw = _load_db_password()
    conn = psycopg2.connect(
        host="aws-1-sa-east-1.pooler.supabase.com",
        port=6543,
        dbname="postgres",
        user="postgres.azhpxhrwhegfysoeqmft",
        password=pw,
        sslmode="require",
    )
    conn.autocommit = True
    cur = conn.cursor()

    sql_005 = ROOT / "sql" / "005_rh_matricula_dim_ponto_tipos.sql"
    sql_schema = ROOT / "sql" / "004_rh_ponto_dia_e_views.sql"
    for path in (sql_005, sql_schema):
        if not path.exists():
            continue
        schema = path.read_text(encoding="utf-8").split("-- AUDITORIA")[0]
        try:
            cur.execute(schema)
            print(f"  OK — schema/views {path.name} aplicados")
        except Exception as e:
            print(f"  AVISO schema {path.name}: {e}")

    print("  Limpando dados FOPA anteriores (Jun/Jul 2026+)...")
    limpar_dados_fopa(cur)

    n_dim = sync_dim_rh(cur, bundle)
    print(f"  OK — dim_rh sincronizado: {n_dim} colaboradores")

    bh_data = [
        (
            r.id_rh, r.competencia, r.setor, r.horas_he_50, r.horas_he_100,
            r.horas_credito, r.horas_debito, r.saldo_mes, r.saldo_acumulado,
        )
        for r in bundle.banco_horas
    ]
    if bh_data:
        execute_batch(
            cur,
            """
            insert into rh_banco_horas (
                id_rh, competencia, setor, horas_he_50, horas_he_100,
                horas_credito, horas_debito, saldo_mes, saldo_acumulado, origem
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,'FOPA_PDF')
            on conflict (id_rh, competencia) do update set
                setor=excluded.setor, horas_he_50=excluded.horas_he_50,
                horas_he_100=excluded.horas_he_100, horas_credito=excluded.horas_credito,
                horas_debito=excluded.horas_debito, saldo_mes=excluded.saldo_mes,
                saldo_acumulado=excluded.saldo_acumulado
            """,
            bh_data,
            page_size=200,
        )
        print(f"  OK — rh_banco_horas: {len(bh_data)} registros")

    bs_data = [
        (s.competencia, s.setor, s.qtd_colaboradores, s.horas_he_100, s.horas_saldo_total)
        for s in bundle.banco_setor
    ]
    if bs_data:
        execute_batch(
            cur,
            """
            insert into rh_banco_horas_setor (
                competencia, setor, qtd_colaboradores, horas_he_100, horas_saldo_total, origem
            ) values (%s,%s,%s,%s,%s,'FOPA_PDF')
            on conflict (competencia, setor) do update set
                qtd_colaboradores=excluded.qtd_colaboradores,
                horas_he_100=excluded.horas_he_100,
                horas_saldo_total=excluded.horas_saldo_total
            """,
            bs_data,
            page_size=100,
        )
        print(f"  OK — rh_banco_horas_setor: {len(bs_data)} registros")

    pd_data = [
        (
            p.id_rh, p.data, p.competencia, p.nome, p.setor, p.cargo,
            p.tipo_dia, p.horas_abonadas, p.horas_debito, p.possui_atestado, p.observacao,
        )
        for p in bundle.ponto_dia
    ]
    if pd_data:
        execute_batch(
            cur,
            """
            insert into rh_ponto_dia (
                id_rh, data, competencia, nome_colaborador, setor, cargo,
                tipo_dia, horas_abonadas, horas_debito, possui_atestado, observacao, origem
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'FOPA_PDF')
            on conflict (id_rh, data, tipo_dia) do update set
                horas_abonadas=excluded.horas_abonadas,
                horas_debito=excluded.horas_debito,
                observacao=excluded.observacao
            """,
            pd_data,
            page_size=300,
        )
        print(f"  OK — rh_ponto_dia: {len(pd_data)} eventos")

    jf_data = [
        (
            j.data_falta, j.id_rh, j.nome_colaborador, j.setor, j.funcao,
            j.tipo_justificativa, j.dias_ausencia, j.possui_atestado, j.motivo,
        )
        for j in bundle.justificativas
    ]
    if jf_data:
        cur.execute(
            "delete from rh_justificativa_faltas where status = 'IMPORTADO' "
            "and data_falta between '2026-06-01' and '2026-07-31'"
        )
        execute_batch(
            cur,
            """
            insert into rh_justificativa_faltas (
                data_falta, id_rh, nome_colaborador, setor, funcao,
                tipo_justificativa, dias_ausencia, possui_atestado, motivo, status
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,'IMPORTADO')
            """,
            jf_data,
            page_size=300,
        )
        print(f"  OK — rh_justificativa_faltas: {len(jf_data)} registros")

    fs_data = [
        (
            f.competencia, f.codigo_cc, f.setor, f.qtd_colaboradores,
            f.total_proventos, f.total_descontos, f.total_liquido, f.total_folha,
            f.horas_he_50, f.valor_he_50, f.horas_he_100, f.valor_he_100,
        )
        for f in bundle.folha_setor
    ]
    if fs_data:
        execute_batch(
            cur,
            """
            insert into rh_folha_setor (
                competencia, codigo_cc, setor, qtd_colaboradores,
                total_proventos, total_descontos, total_liquido, total_folha,
                horas_he_50, valor_he_50, horas_he_100, valor_he_100, origem
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'FOPA_CC')
            on conflict (competencia, setor) do update set
                total_proventos=excluded.total_proventos,
                total_folha=excluded.total_folha,
                horas_he_50=excluded.horas_he_50, valor_he_50=excluded.valor_he_50,
                horas_he_100=excluded.horas_he_100, valor_he_100=excluded.valor_he_100
            """,
            fs_data,
            page_size=50,
        )
        print(f"  OK — rh_folha_setor: {len(fs_data)} centros de custo")

    pm_data = [
        (
            p["id_rh"], p["competencia"], p.get("nome_colaborador"), p.get("setor"),
            p.get("dias_falta", 0), p.get("dias_atraso", 0), p.get("faltas_injustificadas", 0),
            p.get("horas_realizadas", 0), p.get("observacao"),
        )
        for p in bundle.ponto_mensal
    ]
    if pm_data:
        execute_batch(
            cur,
            """
            insert into rh_ponto_mensal (
                id_rh, competencia, nome_colaborador, setor,
                dias_falta, dias_atraso, faltas_injustificadas,
                horas_realizadas, observacao
            ) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on conflict (id_rh, competencia) do update set
                nome_colaborador=excluded.nome_colaborador,
                setor=excluded.setor,
                dias_falta=excluded.dias_falta,
                dias_atraso=excluded.dias_atraso,
                faltas_injustificadas=excluded.faltas_injustificadas,
                horas_realizadas=excluded.horas_realizadas,
                observacao=excluded.observacao
            """,
            pm_data,
            page_size=200,
        )
        print(f"  OK — rh_ponto_mensal: {len(pm_data)} registros")

    pt_data = [
        (
            t["id_rh"], t["competencia"], t.get("setor"),
            t["tipo"], t.get("tipo_descricao"), t["qtd_dias"],
        )
        for t in bundle.ponto_tipos
    ]
    if pt_data:
        execute_batch(
            cur,
            """
            insert into rh_ponto_tipos_mensal (
                id_rh, competencia, setor, tipo, tipo_descricao, qtd_dias, origem
            ) values (%s,%s,%s,%s,%s,%s,'IMPORT_PDF')
            on conflict (id_rh, competencia, tipo) do update set
                setor=excluded.setor,
                tipo_descricao=excluded.tipo_descricao,
                qtd_dias=excluded.qtd_dias
            """,
            pt_data,
            page_size=300,
        )
        print(f"  OK — rh_ponto_tipos_mensal: {len(pt_data)} registros")

    cur.execute("""
        update rh_banco_horas_setor s
        set valor_total = coalesce(f.valor_he_50, 0) + coalesce(f.valor_he_100, 0),
            horas_he_50 = coalesce(f.horas_he_50, s.horas_he_50)
        from rh_folha_setor f
        where s.competencia = f.competencia
          and upper(trim(replace(replace(s.setor, '/', ' / '), '  ', ' ')))
            = upper(trim(replace(replace(f.setor, '/', ' / '), '  ', ' ')))
    """)

    cur.execute("""
        update rh_banco_horas bh
        set valor_total = round(s.valor_total / nullif(s.qtd_colaboradores, 0), 2)
        from rh_banco_horas_setor s
        where bh.competencia = s.competencia
          and bh.setor = s.setor
          and coalesce(s.valor_total, 0) > 0
          and bh.competencia >= '2026-06-01'
    """)

    cur.execute("select count(*) from vw_rh_banco_horas_empresa")
    print(f"\n  Views OK — vw_rh_banco_horas_empresa: {cur.fetchone()[0]} meses")
    cur.execute(
        "select mes_key, qtd_colaboradores, dias_equivalentes_total, valor_banco_total "
        "from vw_rh_banco_horas_empresa order by competencia desc limit 3"
    )
    for row in cur.fetchall():
        print(f"    {row}")

    conn.close()


def resumo(bundle: ImportBundle) -> None:
    print("\n=== RESUMO ===")
    print(f"  Banco horas (colaboradores): {len(bundle.banco_horas)}")
    print(f"  Banco horas (setores):       {len(bundle.banco_setor)}")
    print(f"  Ponto diário (eventos):      {len(bundle.ponto_dia)}")
    print(f"  Justificativas:              {len(bundle.justificativas)}")
    print(f"  Folha por centro de custo:   {len(bundle.folha_setor)}")
    print(f"  Tipos ponto (absenteísmo):   {len(bundle.ponto_tipos)}")
    maq = [s for s in bundle.banco_setor if "MAQUINAS" in norm(s.setor)]
    if maq:
        for s in maq:
            print(f"  Setor {s.setor} ({s.competencia}): saldo {s.horas_saldo_total:.2f} h")
    exame = [j for j in bundle.justificativas if j.tipo_justificativa == "Exame periódico"]
    print(f"  Exame periódico (10/07):      {len(exame)} registros")
    if exame:
        for j in exame[:8]:
            print(f"    · {j.nome_colaborador[:35]} — {j.data_falta.strftime('%d/%m/%Y')}")


def main():
    ap = argparse.ArgumentParser(description="Importa PDFs FOPA → Supabase SIGRH")
    ap.add_argument("--pasta", type=Path, default=PASTA_PADRAO)
    ap.add_argument("--dry-run", action="store_true", help="Só lê PDFs e mostra resumo")
    ap.add_argument("--sql-only", action="store_true", help="Gera SQL sem conectar ao banco")
    args = ap.parse_args()

    print(f"SIGRH — Import Banco de Horas FOPA")
    print(f"Pasta: {args.pasta}\n")

    bundle = load_all(args.pasta)
    resumo(bundle)

    if args.dry_run:
        print("\n(dry-run — nada gravado)")
        return

    sql = gerar_sql(bundle)
    SQL_SAIDA.write_text(sql, encoding="utf-8")
    print(f"\nSQL gerado: {SQL_SAIDA}")

    if args.sql_only:
        print("(sql-only — cole no Supabase ou rode aplicar depois)")
        return

    print("\nGravando no Supabase...")
    aplicar_supabase(bundle)
    print("\nConcluído. Lovable pode consultar:")
    print("  · vw_rh_banco_horas_painel")
    print("  · vw_rh_banco_horas_acumulo_jun_jul")
    print("  · vw_rh_banco_horas_setor_rank")
    print("  · vw_rh_banco_horas_empresa")


if __name__ == "__main__":
    main()
