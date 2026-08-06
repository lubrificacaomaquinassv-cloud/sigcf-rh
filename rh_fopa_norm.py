# -*- coding: utf-8 -*-
"""Normalização compartilhada — FOPA / Painel RH."""
from __future__ import annotations

import re
import unicodedata

# Chave normalizada (sem acento, upper) → nome canônico usado no painel
CANONICAL_SETORES: dict[str, str] = {
    "ADMINISTRATIVO": "ADMINISTRACAO",
    "ADMINISTRACAO": "ADMINISTRACAO",
    "ALMOXARIFADO": "ALMOXARIFADO",
    "AUTOCLAVE": "AUTOCLAVE (INDUSTRIA)",
    "AUTOCLAVE (INDUSTRIA)": "AUTOCLAVE (INDUSTRIA)",
    "INDUSTRIA AUTOCLAVE": "AUTOCLAVE (INDUSTRIA)",
    "CORTE DE EUCALIPTO": "CORTE DE EUCALIPTO",
    "FABRICA DE SAL": "FABRICA DE SAL",
    "HIDRAULICA": "HIDRAULICA",
    "MANUTENCAO GERAL": "MANUTENCAO GERAL",
    "MAQUINAS/TRATORES": "MAQUINAS / TRATORES",
    "MAQUINAS / TRATORES": "MAQUINAS / TRATORES",
    "MAQUINAS TRATORES": "MAQUINAS / TRATORES",
    "OFICINA": "OFICINA",
    "PLANTIO": "PLANTIO",
    "SEDE PECUARIA": "SEDE / PECUARIA",
    "SEDE / PECUARIA": "SEDE / PECUARIA",
    "SEDE/PECUARIA": "SEDE / PECUARIA",
    "SEG. MED. TRABALHO": "SEG. MED. TRABALHO",
    "SEG MED TRABALHO": "SEG. MED. TRABALHO",
    "SEGURANCA E MEDICINA DO TRABALHO": "SEG. MED. TRABALHO",
    "VEICULOS": "VEICULOS",
    "VIVEIRO FLORESTAL": "VIVEIRO FLORESTAL",
    "RETIRO AGUA BRANCA": "RETIRO AGUA BRANCA",
    "RETIRO BARRA DO CERVO": "RETIRO BARRA DO CERVO",
    "RETIRO CORREGO DO CAMPO": "RETIRO CORREGO DO CAMPO",
    "RETIRO EUCALIPTO": "RETIRO EUCALIPTO",
    "RETIRO POCO AZUL": "RETIRO POCO AZUL",
    "RETIRO POÇO AZUL": "RETIRO POCO AZUL",
    "RETIRO TAQUARUSSU": "RETIRO TAQUARUSSU",
    "PECUIARIA": "SEDE / PECUARIA",
}

SETOR_INVALIDO = {"GERAL", "DA EMPRESA", "TOTAL", ""}

TIME_TOKEN = re.compile(r"-?\d{1,4}:\d{2}")
BR_MONEY = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")


def norm(s: str) -> str:
    t = unicodedata.normalize("NFKD", str(s or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.strip().upper()


def normalizar_setor(setor: str | None) -> str | None:
    if not setor or not str(setor).strip():
        return None
    k = norm(setor)
    if k in SETOR_INVALIDO:
        return None
    if k in CANONICAL_SETORES:
        return CANONICAL_SETORES[k]
    if k.startswith("RETIRO "):
        return k
    return k


def extract_times(line: str) -> tuple[str, list[str]]:
    """Extrai tokens HH:MM (suporta >999h, ex. 1255:15) da linha."""
    times = TIME_TOKEN.findall(line)
    rest = line
    for t in times:
        idx = rest.rfind(t)
        if idx >= 0:
            rest = (rest[:idx] + rest[idx + len(t):]).strip()
    return rest, times


def parse_hhmm_to_decimal(s: str) -> float:
    s = str(s).strip()
    if not s or s == "—":
        return 0.0
    neg = s.startswith("-")
    s = s.lstrip("-")
    if ":" not in s:
        return 0.0
    h, m = s.split(":", 1)
    v = int(h) + int(m) / 60.0
    return -v if neg else v


def parse_br_money(s: str) -> float:
    s = str(s).strip()
    if not s:
        return 0.0
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_he_linha(linha: str, codigo: str) -> tuple[float, float]:
    """Retorna (horas_ref, valor_r$) de linha 257/259 do centro de custo."""
    if not linha.strip().startswith(codigo):
        return 0.0, 0.0
    nums = BR_MONEY.findall(linha)
    if len(nums) >= 2:
        return parse_br_money(nums[0]), parse_br_money(nums[1])
    return 0.0, 0.0


def tipo_ponto_para_app(tipo_dia: str) -> tuple[str, str]:
    """Mapeia tipo do cartão-ponto para rh_ponto_tipos_mensal."""
    m = {
        "FALTA": ("FALTA_INJUSTIFICADA", "Falta injustificada"),
        "ATESTADO MEDICO": ("ATESTADO_MEDICO", "Atestado médico"),
        "FERIAS": ("FERIAS", "Férias"),
        "AFASTAMENTO": ("AFASTAMENTO_INSS", "Afastamento INSS"),
        "EXAME PERIODICO": ("EXAME_PERIODICO", "Exame periódico"),
        "DISPENSA": ("DISPENSA", "Dispensa"),
        "ABONO": ("ABONO", "Abono"),
        "BANCO": ("BANCO", "Compensação banco de horas"),
        "FOLGA": ("FOLGA", "Folga"),
    }
    return m.get(tipo_dia, (tipo_dia.replace(" ", "_").upper(), tipo_dia.title()))
