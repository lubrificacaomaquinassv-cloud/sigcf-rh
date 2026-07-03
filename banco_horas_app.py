# -*- coding: utf-8 -*-
"""Painel exclusivo de Banco de Horas — SANTA VERGÍNIA.

Mostra apenas quantidade de horas, saldo do banco e valor estimado caso a
empresa decida pagar o saldo. NÃO exibe folha de pagamento, salário bruto/
líquido, encargos ou descontos — esse é um painel separado do SIGRH de
justificativa de faltas (rh_app.py).
"""
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client
from sigcf_auth import exigir_acesso, logo_html

st.set_page_config(
    page_title="Banco de Horas — SANTA VERGÍNIA",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
T_BANCO = "rh_banco_horas"
T_BANCO_SETOR = "rh_banco_horas_setor"
T_PONTO = "rh_ponto_mensal"
T_PONTO_TIPOS = "rh_ponto_tipos_mensal"
DIM_RH = "dim_rh"

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

exigir_acesso("BANCO DE HORAS — SANTA VERGÍNIA", "Painel exclusivo de banco de horas")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
.stApp{
 background:linear-gradient(rgba(10,20,9,0.68),rgba(10,20,9,0.82)),
 url('__BG__') center center/cover no-repeat fixed!important;}
[data-testid="stAppViewContainer"]{background:transparent!important;}
[data-testid="stSidebar"]{background:rgba(10,20,9,0.96)!important;border-right:1px solid #1e2e1c!important;}
[data-testid="stSidebar"] *{color:#e8edd0!important;}
[data-testid="stHeader"]{background:rgba(10,20,9,0.45)!important;}
.block-container{background:transparent!important;max-width:1180px!important;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
h1{font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ab892!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#9ab892;
 border-left:4px solid #5a9452;padding-left:10px;margin:8px 0 12px;}
div[data-baseweb="select"] > div{
 background:#dce6d2!important;border:1px solid #4a6644!important;
 color:#1a2818!important;border-radius:8px!important;}
div[data-baseweb="select"] div{color:#1a2818!important;}
ul[data-testid="stSelectboxVirtualDropdown"], div[data-baseweb="popover"] ul{background:#e8edd0!important;}
div[data-baseweb="popover"] li{color:#1a2818!important;}
div[data-testid="stMetric"]{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:10px;padding:10px 14px;}
div[data-testid="stMetric"] label{color:#9ab892!important;}
div[data-testid="stMetricValue"]{color:#8ec486!important;font-family:'Barlow Condensed',sans-serif;}
</style>
""".replace("__BG__", BG_URL), unsafe_allow_html=True)


def ler_credenciais_supabase() -> tuple[str, str]:
    url = st.secrets.get("SUPABASE_URL") or (st.secrets.get("supabase", {}) or {}).get("url")
    key = st.secrets.get("SUPABASE_KEY") or (st.secrets.get("supabase", {}) or {}).get("key")
    return str(url or "").strip(), str(key or "").strip()


url_sb, key_sb = ler_credenciais_supabase()
if not url_sb or not key_sb:
    st.error("Secrets do Supabase não encontrados neste app (SUPABASE_URL / SUPABASE_KEY).")
    st.stop()

try:
    sb = create_client(url_sb, key_sb)
except Exception as exc:
    st.error("Não foi possível conectar ao Supabase.")
    st.caption(str(exc))
    st.stop()


def fmt_moeda(valor) -> str:
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def competencia_str(ano: int, mes: int) -> str:
    return f"{int(ano):04d}-{int(mes):02d}-01"


def dark_table(df: pd.DataFrame, height: int = 320):
    if df.empty:
        st.info("Nenhum registro.")
        return
    rows = "".join(
        "<tr>" + "".join(
            f'<td style="padding:6px 10px;border-bottom:1px solid #1e2e1c;'
            f'color:#e8edd0;font-size:12px;">{v}</td>' for v in row) + "</tr>"
        for _, row in df.iterrows())
    headers = "".join(
        f'<th style="padding:7px 10px;background:#111c10;color:#8aab80;font-size:10px;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:1px;'
        f'border-bottom:2px solid #1e2e1c;">{c}</th>' for c in df.columns)
    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #1e2e1c;border-radius:10px;">'
        f'<div style="max-height:{height}px;overflow-y:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:#0d180c;'
        f'font-family:Barlow Condensed,sans-serif;"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div>',
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=15)
def carregar_funcionarios_rh():
    res = sb.table(DIM_RH).select("id_rh, nome, setor, cargo").eq("ativo", True).order("nome").execute()
    return res.data or []


@st.cache_data(ttl=15)
def carregar_banco_horas(comp: str):
    try:
        return sb.table(T_BANCO).select("*").eq("competencia", comp).order("setor").execute().data or []
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_banco_setor(comp: str):
    try:
        return sb.table(T_BANCO_SETOR).select("*").eq("competencia", comp).order("setor").execute().data or []
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_ponto_mensal(comp: str):
    try:
        return sb.table(T_PONTO).select("*").eq("competencia", comp).order("setor").execute().data or []
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_ponto_tipos(comp: str):
    try:
        return sb.table(T_PONTO_TIPOS).select("*").eq("competencia", comp).execute().data or []
    except Exception:
        return None


def _render_banco_horas(rows_banco, rows_setor, nomes_rh, cargos_rh):
    qtde_gerada_mes = sum(float(r.get("saldo_mes") or 0) for r in rows_banco)
    saldo_acumulado_total = sum(float(r.get("saldo_acumulado") or 0) for r in rows_banco)
    valor_total_geral = sum(float(r.get("valor_total") or 0) for r in rows_banco)

    horas_credito_total = sum(float(r.get("horas_credito") or 0) for r in rows_banco)
    horas_debito_total = sum(float(r.get("horas_debito") or 0) for r in rows_banco)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Colaboradores", len(rows_banco))
    k2.metric("Qtde HE gerada no mês (líquido)", f"{qtde_gerada_mes:.1f} h")
    k3.metric("Saldo acumulado (banco)", f"{saldo_acumulado_total:.1f} h")
    k4.metric("Valor total se pago", fmt_moeda(valor_total_geral))

    with st.expander("ℹ️ Como o número líquido do mês é composto?"):
        d1, d2, d3 = st.columns(3)
        d1.metric("Horas geradas (crédito)", f"+{horas_credito_total:.1f} h")
        d2.metric("Horas debitadas (banco/ajustes)", f"-{horas_debito_total:.1f} h")
        d3.metric("Líquido do período", f"{qtde_gerada_mes:.1f} h")
        st.caption(
            "O líquido pode ficar negativo quando o total debitado (ex.: sábados compensados "
            "via 'Banco' e ajustes negativos) supera as horas extras geradas no período. "
            "O saldo **acumulado** continua positivo porque soma os meses anteriores."
        )

    st.divider()

    col_mini, col_rank = st.columns([1, 1.3])

    with col_mini:
        st.markdown('<div class="sec">💼 Saldo do banco por setor</div>', unsafe_allow_html=True)
        if rows_setor:
            pares = sorted(
                ((r.get("setor") or "—", float(r.get("horas_saldo_total") or 0)) for r in rows_setor),
                key=lambda p: p[1], reverse=True,
            )
        else:
            acc = {}
            for r in rows_banco:
                s = r.get("setor") or "—"
                acc[s] = acc.get(s, 0.0) + float(r.get("saldo_acumulado") or 0)
            pares = sorted(acc.items(), key=lambda p: p[1], reverse=True)

        linhas_html = "".join(
            f'<div style="display:flex;justify-content:space-between;padding:5px 2px;'
            f'border-bottom:1px solid #1e2e1c;font-size:13px;">'
            f'<span style="color:#e8edd0;">{setor}</span>'
            f'<span style="color:#8ec486;font-weight:700;">{saldo:.1f} h</span></div>'
            for setor, saldo in pares
        )
        st.markdown(
            f'<div style="background:rgba(13,24,12,0.88);border:1px solid #2a3d28;'
            f'border-radius:10px;padding:12px 16px;max-height:300px;overflow-y:auto;">'
            f'{linhas_html}</div>',
            unsafe_allow_html=True,
        )

    with col_rank:
        st.markdown('<div class="sec">🔎 Consulta individual — maior → menor saldo</div>', unsafe_allow_html=True)
        ranking = sorted(rows_banco, key=lambda r: float(r.get("saldo_acumulado") or 0), reverse=True)
        opcoes_rank = [
            f"{nomes_rh.get(r['id_rh'], r['id_rh'])} — {float(r.get('saldo_acumulado') or 0):.1f} h"
            for r in ranking
        ]
        idx_sel = st.selectbox(
            "Colaborador (ordem decrescente de saldo)",
            options=list(range(len(opcoes_rank))),
            format_func=lambda i: opcoes_rank[i],
            key="sel_banco_ranking",
        )
        r_sel = ranking[idx_sel]
        vs1, vs2 = st.columns(2)
        vs1.metric("Quantidade (saldo)", f"{float(r_sel.get('saldo_acumulado') or 0):.1f} h")
        vs2.metric("Valor se pago", fmt_moeda(r_sel.get("valor_total")))
        vs3, vs4 = st.columns(2)
        vs3.metric("Setor", r_sel.get("setor") or "—")
        vs4.metric("Função", cargos_rh.get(r_sel["id_rh"], "—"))

    st.divider()
    st.markdown('<div class="sec">🏢 Setores — quantidade de horas e valor</div>', unsafe_allow_html=True)
    if rows_setor:
        df_setor = pd.DataFrame(rows_setor).rename(columns={
            "setor": "Setor", "qtd_colaboradores": "Colaboradores",
            "horas_saldo_total": "Saldo (h)", "valor_total": "Valor total",
        })
        df_setor = df_setor[["Setor", "Colaboradores", "Saldo (h)", "Valor total"]]
        df_setor["Saldo (h)"] = df_setor["Saldo (h)"].astype(float).round(1)
        df_setor["Valor total"] = df_setor["Valor total"].astype(float).map(fmt_moeda)
        df_setor = df_setor.sort_values("Saldo (h)", ascending=False)
        dark_table(df_setor, height=280)

    st.markdown('<div class="sec">👤 Colaboradores — do maior para o menor saldo</div>', unsafe_allow_html=True)
    df_ind = pd.DataFrame([
        {
            "Colaborador": nomes_rh.get(r["id_rh"], r["id_rh"]),
            "Setor": r.get("setor") or "—",
            "Função": cargos_rh.get(r["id_rh"], "—"),
            "Saldo (h)": round(float(r.get("saldo_acumulado") or 0), 1),
            "Gerado no mês (h)": round(float(r.get("saldo_mes") or 0), 1),
            "Valor se pago": fmt_moeda(r.get("valor_total")),
        }
        for r in ranking
    ])
    dark_table(df_ind, height=420)


TIPOS_AFASTAMENTO_REAL = {
    "FALTA_INJUSTIFICADA", "ATESTADO_MEDICO", "FERIAS",
    "AFASTAMENTO_INSS", "SUSPENSAO", "EXAME_PERIODICO",
}


def _render_absenteismo(rows_ponto, rows_tipos, nomes_rh, cargos_rh):
    total_colaboradores = len(rows_ponto)
    ids_afastados = {t["id_rh"] for t in rows_tipos if t.get("tipo") in TIPOS_AFASTAMENTO_REAL}
    dias_falta_total = sum(float(r.get("dias_falta") or 0) for r in rows_ponto)
    faltas_injust_total = sum(float(r.get("faltas_injustificadas") or 0) for r in rows_ponto)
    exame_periodico_ids = {t["id_rh"] for t in rows_tipos if t.get("tipo") == "EXAME_PERIODICO"}

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Nº de afastados no mês", len(ids_afastados))
    k2.metric("Faltas injustificadas (dias)", f"{faltas_injust_total:.0f}")
    k3.metric("Dias de falta (total)", f"{dias_falta_total:.0f}")
    k4.metric("Ausentes exame periódico (11/06)", len(exame_periodico_ids))
    st.caption(
        f"Base: {total_colaboradores} colaboradores com registro de ponto na competência. "
        "'Nº de afastados' conta colaboradores com falta injustificada, atestado médico, férias, "
        "afastamento INSS, suspensão ou exame periódico — não inclui dispensas/folgas administrativas "
        "rotineiras (ex.: sábado dispensado), que aparecem à parte na tabela de tipos abaixo."
    )

    st.divider()

    col_tipos, col_rank = st.columns([1.2, 1])

    with col_tipos:
        st.markdown('<div class="sec">📋 Tipos de justificativa/ausência</div>', unsafe_allow_html=True)
        if rows_tipos:
            agg = {}
            for t in rows_tipos:
                desc = t.get("tipo_descricao") or t.get("tipo")
                a = agg.setdefault(desc, {"dias": 0.0, "colabs": set()})
                a["dias"] += float(t.get("qtd_dias") or 0)
                a["colabs"].add(t["id_rh"])
            df_tipos = pd.DataFrame([
                {"Justificativa": desc, "Dias": v["dias"], "Colaboradores": len(v["colabs"])}
                for desc, v in agg.items()
            ]).sort_values("Dias", ascending=False)
            df_tipos["Dias"] = df_tipos["Dias"].round(1)
            dark_table(df_tipos, height=320)
        else:
            st.info("Nenhuma ocorrência de ausência/justificativa lançada nesta competência.")

    with col_rank:
        st.markdown('<div class="sec">🔎 Consulta individual — ocorrências</div>', unsafe_allow_html=True)
        ranking_ponto = sorted(rows_ponto, key=lambda r: float(r.get("dias_falta") or 0), reverse=True)
        opcoes_rank = [
            f"{nomes_rh.get(r['id_rh'], r['id_rh'])} — {float(r.get('dias_falta') or 0):.0f} dia(s) de falta"
            for r in ranking_ponto
        ]
        idx_sel = st.selectbox(
            "Colaborador",
            options=list(range(len(opcoes_rank))),
            format_func=lambda i: opcoes_rank[i],
            key="sel_absenteismo_ranking",
        )
        r_sel = ranking_ponto[idx_sel]
        vs1, vs2 = st.columns(2)
        vs1.metric("Dias de falta", f"{float(r_sel.get('dias_falta') or 0):.0f}")
        vs2.metric("Faltas injustificadas", f"{float(r_sel.get('faltas_injustificadas') or 0):.0f}")
        vs3, vs4 = st.columns(2)
        vs3.metric("Setor", r_sel.get("setor") or "—")
        vs4.metric("Função", cargos_rh.get(r_sel["id_rh"], "—"))
        tipos_sel = [t for t in rows_tipos if t["id_rh"] == r_sel["id_rh"]]
        if tipos_sel:
            st.caption("Justificativas: " + "; ".join(
                f"{t.get('tipo_descricao')} ({float(t.get('qtd_dias') or 0):.0f}d)" for t in tipos_sel
            ))

    st.divider()
    st.markdown('<div class="sec">👤 Colaboradores com ausência — do maior para o menor</div>', unsafe_allow_html=True)
    df_ind = pd.DataFrame([
        {
            "Colaborador": nomes_rh.get(r["id_rh"], r["id_rh"]),
            "Setor": r.get("setor") or "—",
            "Função": cargos_rh.get(r["id_rh"], "—"),
            "Dias úteis": r.get("dias_uteis") or 0,
            "Dias trabalhados": round(float(r.get("dias_trabalhados") or 0), 1),
            "Dias de falta": round(float(r.get("dias_falta") or 0), 1),
            "Faltas injustificadas": round(float(r.get("faltas_injustificadas") or 0), 1),
        }
        for r in ranking_ponto if float(r.get("dias_falta") or 0) > 0
    ])
    dark_table(df_ind, height=380)


col_logo, col_titulo = st.columns([1.1, 5.9])
with col_logo:
    st.markdown(logo_html(110), unsafe_allow_html=True)
with col_titulo:
    st.title("⏱️ Banco de Horas")
    st.caption("SANTA VERGÍNIA · SALDO, GERAÇÃO MENSAL E VALOR ESTIMADO POR SETOR/COLABORADOR")

st.divider()

with st.sidebar:
    st.markdown("### Competência")
    hoje = date.today()
    c1, c2 = st.columns(2)
    with c1:
        mes_nome = st.selectbox("Mês", MESES_PT, index=5, key="bh_mes")
    with c2:
        ano = st.number_input("Ano", min_value=2024, max_value=2030, value=2026, step=1, key="bh_ano")
    mes = MESES_PT.index(mes_nome) + 1
    comp = competencia_str(ano, mes)
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Competência: **{mes:02d}/{ano}**")

funcionarios_rh = carregar_funcionarios_rh()
nomes_rh = {f["id_rh"]: f["nome"] for f in funcionarios_rh}
cargos_rh = {f["id_rh"]: (f.get("cargo") or "—") for f in funcionarios_rh}

tab_banco, tab_absenteismo = st.tabs(["⏱️ Banco de Horas", "📊 Absenteísmo"])

with tab_banco:
    rows_banco = carregar_banco_horas(comp)
    rows_setor = carregar_banco_setor(comp)

    if rows_banco is None:
        st.error("Tabela `rh_banco_horas` não encontrada no Supabase. Rode `sql/003_rh_banco_horas_folha_ponto.sql`.")
    elif not rows_banco:
        st.info("Sem dados de banco de horas lançados para esta competência.")
    else:
        _render_banco_horas(rows_banco, rows_setor, nomes_rh, cargos_rh)

with tab_absenteismo:
    rows_ponto = carregar_ponto_mensal(comp)
    rows_tipos = carregar_ponto_tipos(comp)

    if rows_ponto is None:
        st.error("Tabela `rh_ponto_mensal` não encontrada no Supabase. Rode `sql/003_rh_banco_horas_folha_ponto.sql`.")
    elif not rows_ponto:
        st.info("Sem dados de ponto/absenteísmo lançados para esta competência.")
    else:
        _render_absenteismo(rows_ponto, rows_tipos or [], nomes_rh, cargos_rh)
