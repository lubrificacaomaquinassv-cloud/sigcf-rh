import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from calendar import monthrange
from supabase import create_client, Client
from sigcf_auth import exigir_acesso, logo_html

st.set_page_config(
    page_title="SIGRH — SANTA VERGÍNIA",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
TABELA = "rh_justificativa_faltas"
T_BANCO = "rh_banco_horas"
T_BANCO_SETOR = "rh_banco_horas_setor"
T_FOLHA = "rh_folha_mensal"
T_PONTO = "rh_ponto_mensal"
DIAS_UTEIS_MES = 22

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

MENU_SIGRH = [
    "🏠 Início",
    "📋 Justificativas",
    "📊 Absenteísmo",
    "⏱️ Banco de horas",
    "💰 Folha & encargos",
    "🕐 Ponto × Faltas",
    "📈 Demonstrativo RH",
]


def link_instagram(text: str = "@fazendasantaverginia") -> str:
    icon = (
        '<img class="insta-ico" src="https://cdn.simpleicons.org/instagram/8ec486" '
        'width="17" height="17" alt="" loading="lazy">'
    )
    return (
        f'<a class="insta-link" href="https://www.instagram.com/fazendasantaverginia" '
        f'target="_blank" rel="noopener">{icon}{text}</a>'
    )

TIPOS_JUSTIFICATIVA = [
    "Atestado médico",
    "Declaração / comparecimento",
    "Licença",
    "Falta justificada",
    "Falta injustificada",
    "Afastamento INSS",
    "Outros",
]

SETORES = [
    "Máquinas",
    "Pecuária",
    "Florestal",
    "Oficina",
    "Administração",
    "Refeitório",
    "RH",
    "Outros",
]

DIM_RH = "dim_rh"

exigir_acesso("SIGRH — SANTA VERGÍNIA")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
.stApp{
 background:linear-gradient(rgba(10,20,9,0.68),rgba(10,20,9,0.82)),
 url('__BG__') center center/cover no-repeat fixed!important;}
[data-testid="stAppViewContainer"]{background:transparent!important;}
[data-testid="stSidebar"]{
 background:rgba(10,20,9,0.96)!important;border-right:1px solid #1e2e1c!important;}
[data-testid="stSidebar"] *{color:#e8edd0!important;}
[data-testid="stSidebar"] .stRadio label{font-family:'Barlow Condensed',sans-serif;font-size:14px;}
[data-testid="stHeader"]{background:rgba(10,20,9,0.45)!important;}
.block-container{background:transparent!important;max-width:1180px!important;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
h1{font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ab892!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#9ab892;
 border-left:4px solid #5a9452;padding-left:10px;margin:8px 0 12px;}
.logo-frame{background:linear-gradient(145deg,#0a1628,#0d2040);border:2px solid #c9a227;
 border-radius:12px;padding:5px;display:inline-block;box-shadow:0 4px 18px rgba(0,0,0,.45);}
.logo-frame img{display:block;border-radius:8px;}
.ctx-box{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:12px;padding:14px 16px;margin-bottom:12px;}
.hub-card{background:rgba(17,28,16,0.86);border:1px solid #2a3d28;border-radius:14px;padding:18px 14px;
 text-align:center;min-height:118px;transition:border-color .2s;}
.hub-card.active{border-color:rgba(90,148,82,0.85);border-top:3px solid #5a9452;}
.hub-card.soon{opacity:.55;border-style:dashed;}
.hub-card .ico{font-size:28px;line-height:1;margin-bottom:8px;}
.hub-card .tit{font-family:'Barlow Condensed',sans-serif;font-size:13px;font-weight:700;
 color:#e8edd0;text-transform:uppercase;letter-spacing:.5px;line-height:1.25;}
.hub-card .tag{font-size:9px;font-weight:700;letter-spacing:1px;margin-top:8px;
 display:inline-block;padding:3px 10px;border-radius:10px;}
.hub-card.active .tag{background:rgba(26,58,24,0.9);color:#8ec486;border:1px solid #5a9452;}
.hub-card.soon .tag{background:#1a1a10;color:#8aab80;border:1px solid #3a4a38;}
.insta-link{display:inline-flex;align-items:center;gap:6px;color:#8ec486!important;
 text-decoration:none;font-weight:600;}
.insta-link:hover{color:#a8d8a0!important;text-decoration:none;}
.insta-ico{width:17px;height:17px;flex-shrink:0;}

.stTextInput input,.stNumberInput input,.stTextArea textarea,
[data-testid="stDateInput"] input{
 background:#dce6d2!important;color:#1a2818!important;
 border:1px solid #4a6644!important;border-radius:8px!important;}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus,
[data-testid="stDateInput"] input:focus{
 border-color:#6fcf60!important;box-shadow:0 0 0 1px #6fcf6044!important;}
div[data-baseweb="select"] > div{
 background:#dce6d2!important;border:1px solid #4a6644!important;
 color:#1a2818!important;border-radius:8px!important;}
div[data-baseweb="select"] div{color:#1a2818!important;}
div[data-baseweb="select"] svg{fill:#4a6644!important;}
ul[data-testid="stSelectboxVirtualDropdown"],
div[data-baseweb="popover"] ul{background:#e8edd0!important;}
div[data-baseweb="popover"] li{color:#1a2818!important;}
[data-testid="stNumberInput"] button{
 background:#cdd9c4!important;border-color:#4a6644!important;color:#1a2818!important;}
[data-testid="stForm"]{
 background:rgba(13,24,12,0.88)!important;border:1px solid #2a3d28!important;
 border-radius:12px;padding:12px 16px;}
div[data-testid="stMetric"]{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:10px;padding:10px 14px;}
div[data-testid="stMetric"] label{color:#9ab892!important;}
div[data-testid="stMetricValue"]{color:#8ec486!important;font-family:'Barlow Condensed',sans-serif;}
.stTabs [data-baseweb="tab-list"]{background:rgba(13,24,12,0.88);border-bottom:1px solid #2a3d28;gap:8px;}
.stTabs [data-baseweb="tab"]{
 color:#9ab892!important;font-family:'Barlow Condensed',sans-serif;font-weight:600;}
.stTabs [aria-selected="true"]{color:#e8edd0!important;border-bottom-color:#5a9452!important;}
.stTabs [data-baseweb="tab-highlight"]{background-color:#5a9452!important;}
div[data-testid="stCheckbox"] label span{color:#e8edd0!important;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fa864!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1.5px;
 text-transform:uppercase;border-radius:8px;min-height:44px;}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#3d8534!important;}

@media (max-width:768px){
 .block-container{padding-left:0.75rem!important;padding-right:0.75rem!important;padding-top:1rem!important;}
 h1{font-size:1.55rem!important;line-height:1.15!important;}
 div[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:0.35rem!important;}
 div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
  min-width:calc(50% - 0.5rem)!important;flex:1 1 calc(50% - 0.5rem)!important;}
 div[data-testid="stHorizontalBlock"]:has(.hub-card) > div[data-testid="column"]{
  min-width:100%!important;flex:1 1 100%!important;}
 .hub-card{min-height:88px;padding:14px 10px;}
 .stTextInput input,.stNumberInput input,.stTextArea textarea,
 [data-testid="stDateInput"] input{font-size:16px!important;min-height:44px!important;}
 div[data-baseweb="select"] > div{min-height:44px!important;}
 [data-testid="stFormSubmitButton"] button{width:100%!important;}
}
</style>
""".replace("__BG__", BG_URL), unsafe_allow_html=True)


def dark_table(df, height=320):
    if df.empty:
        st.info("Nenhum registro.")
        return
    rows = "".join(
        "<tr>" + "".join(
            f'<td style="padding:6px 10px;border-bottom:1px solid #1e2e1c;'
            f'color:#e8edd0;font-size:12px;">{v}</td>'
            for v in row) + "</tr>"
        for _, row in df.iterrows())
    headers = "".join(
        f'<th style="padding:7px 10px;background:#111c10;color:#8aab80;font-size:10px;'
        f'font-weight:700;text-transform:uppercase;letter-spacing:1px;'
        f'border-bottom:2px solid #1e2e1c;">{c}</th>'
        for c in df.columns)
    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #1e2e1c;border-radius:10px;">'
        f'<div style="max-height:{height}px;overflow-y:auto;">'
        f'<table style="width:100%;border-collapse:collapse;background:#0d180c;'
        f'font-family:Barlow Condensed,sans-serif;"><thead><tr>{headers}</tr></thead>'
        f'<tbody>{rows}</tbody></table></div></div>',
        unsafe_allow_html=True,
    )


def gerar_excel(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def fmt_data(d) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(d)


def ler_credenciais_supabase() -> tuple[str, str]:
    """Aceita secrets no formato plano (SIGCF) ou seção [supabase]."""
    url = (
        st.secrets.get("SUPABASE_URL")
        or st.secrets.get("supabase_url")
        or (st.secrets.get("supabase", {}) or {}).get("url")
        or (st.secrets.get("supabase", {}) or {}).get("SUPABASE_URL")
    )
    key = (
        st.secrets.get("SUPABASE_KEY")
        or st.secrets.get("supabase_key")
        or (st.secrets.get("supabase", {}) or {}).get("key")
        or (st.secrets.get("supabase", {}) or {}).get("SUPABASE_KEY")
    )
    return str(url or "").strip(), str(key or "").strip()


def diagnosticar_secrets():
    try:
        chaves = list(st.secrets.keys())
    except Exception:
        chaves = []
    st.error("Secrets do Supabase não encontrados neste app.")
    st.markdown("**Chaves detectadas no Streamlit:** " + (", ".join(chaves) if chaves else "nenhuma"))
    st.markdown(
        """
        Cole em **Streamlit Cloud → seu app sigcf-rh → Settings → Secrets → Save → Reboot app**:

        ```toml
        SUPABASE_URL = "https://azhpxhrwhegfysoeqmft.supabase.co"
        SUPABASE_KEY = "eyJ...sua-anon-key..."
        APP_PIN = "SV2026!x"
        ```

        **Atenção:** sem colchetes `[ ]` no topo, aspas normais `"`, e salvar no app **sigcf-rh** (não em outro).
        """
    )


url_sb, key_sb = ler_credenciais_supabase()
if not url_sb or not key_sb:
    diagnosticar_secrets()
    st.stop()

try:
    sb = create_client(url_sb, key_sb)
except Exception as exc:
    st.error("Não foi possível conectar ao Supabase.")
    st.caption(str(exc))
    st.stop()


@st.cache_data(ttl=120)
def carregar_funcionarios_rh():
    res = (
        sb.table(DIM_RH)
        .select("id_rh, nome, setor, cargo")
        .eq("ativo", True)
        .order("nome")
        .execute()
    )
    return res.data or []


@st.cache_data(ttl=15)
def carregar_faltas(data_ini=None, data_fim=None):
    query = sb.table(TABELA).select("*").order("data_falta", desc=True).order("criado_em", desc=True)
    if data_ini:
        query = query.gte("data_falta", str(data_ini))
    if data_fim:
        query = query.lte("data_falta", str(data_fim))
    return query.limit(1000).execute().data or []


def funcionario_por_nome(nome: str, lista: list) -> dict | None:
    for c in lista:
        if c.get("nome") == nome:
            return c
    return None


def indice_setor(setor: str) -> int:
    s = (setor or "Outros").strip()
    if s in SETORES:
        return SETORES.index(s)
    return SETORES.index("Outros")


def calcular_absenteismo(rows: list, num_colaboradores: int, dias_uteis: int) -> dict:
    if num_colaboradores <= 0 or dias_uteis <= 0:
        return {"indice": 0.0, "total_dias": 0.0, "denominador": 0}
    total_dias = sum(float(r.get("dias_ausencia") or 0) for r in rows)
    denominador = num_colaboradores * dias_uteis
    indice = (total_dias / denominador) * 100 if denominador else 0.0
    return {"indice": indice, "total_dias": total_dias, "denominador": denominador}


def df_faltas(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    out = []
    for r in rows:
        out.append({
            "Data": fmt_data(r.get("data_falta")),
            "Colaborador": r.get("nome_colaborador", ""),
            "Setor": r.get("setor") or "",
            "Tipo": r.get("tipo_justificativa", ""),
            "Dias": r.get("dias_ausencia", 1),
            "Atestado": "Sim" if r.get("possui_atestado") else "Não",
            "Motivo": r.get("motivo", ""),
            "Status": r.get("status", ""),
        })
    return pd.DataFrame(out)


def fmt_moeda(valor) -> str:
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        v = 0.0
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def competencia_str(ano: int, mes: int) -> str:
    return f"{int(ano):04d}-{int(mes):02d}-01"


def seletor_competencia(prefix: str = "comp", mes_default: int | None = None, ano_default: int | None = None):
    hoje = date.today()
    mes_idx = (mes_default or hoje.month) - 1
    ano_val = ano_default or hoje.year
    c1, c2 = st.columns(2)
    with c1:
        mes_nome = st.selectbox("Mês", MESES_PT, index=mes_idx, key=f"{prefix}_mes")
    with c2:
        ano = st.number_input("Ano", min_value=2024, max_value=2030, value=ano_val, step=1, key=f"{prefix}_ano")
    mes = MESES_PT.index(mes_nome) + 1
    return competencia_str(ano, mes), mes, int(ano)


@st.cache_data(ttl=15)
def carregar_banco_horas(comp: str):
    try:
        return (
            sb.table(T_BANCO).select("*").eq("competencia", comp).order("setor").order("id_rh").execute().data or []
        )
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_banco_setor(comp: str):
    try:
        return (
            sb.table(T_BANCO_SETOR).select("*").eq("competencia", comp).order("setor").execute().data or []
        )
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_folha(comp: str):
    try:
        return (
            sb.table(T_FOLHA).select("*").eq("competencia", comp).order("setor").order("id_rh").execute().data or []
        )
    except Exception:
        return None


@st.cache_data(ttl=15)
def carregar_ponto(comp: str):
    try:
        return (
            sb.table(T_PONTO).select("*").eq("competencia", comp).order("setor").order("nome_colaborador").execute().data or []
        )
    except Exception:
        return None


def kpi_banco(rows: list) -> dict:
    if not rows:
        return {
            "horas_saldo": 0.0, "valor_total": 0.0, "he50": 0.0, "he100": 0.0,
            "colab": 0, "saldo_acumulado_total": 0.0,
        }
    return {
        "horas_saldo": sum(float(r.get("saldo_mes") or 0) for r in rows),
        "valor_total": sum(float(r.get("valor_total") or 0) for r in rows),
        "he50": sum(float(r.get("horas_he_50") or 0) for r in rows),
        "he100": sum(float(r.get("horas_he_100") or 0) for r in rows),
        "colab": len(rows),
        "saldo_acumulado_total": sum(float(r.get("saldo_acumulado") or 0) for r in rows),
    }


def df_banco_por_setor(rows: list) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    agg = (
        df.groupby("setor", dropna=False)
        .agg(
            Colaboradores=("id_rh", "count"),
            HE_50=("horas_he_50", "sum"),
            HE_100=("horas_he_100", "sum"),
            Saldo_h=("saldo_mes", "sum"),
            Valor_total=("valor_total", "sum"),
        )
        .reset_index()
        .rename(columns={"setor": "Setor"})
    )
    for c in ("HE_50", "HE_100", "Saldo_h"):
        agg[c] = agg[c].astype(float).round(1)
    agg["Valor_total"] = agg["Valor_total"].astype(float).round(2)
    return agg.sort_values("Saldo_h", ascending=False)


def cruzar_ponto_faltas(ponto_rows: list, falta_rows: list, dias_uteis: int) -> pd.DataFrame:
    just_por_rh = {}
    for r in falta_rows:
        ch = r.get("id_rh") or r.get("nome_colaborador")
        just_por_rh[ch] = just_por_rh.get(ch, 0) + float(r.get("dias_ausencia") or 0)
    out = []
    for p in ponto_rows:
        ch = p.get("id_rh")
        dias_falta_ponto = float(p.get("dias_falta") or 0)
        dias_just = just_por_rh.get(ch, 0)
        gap = max(dias_falta_ponto - dias_just, 0)
        out.append({
            "Colaborador": p.get("nome_colaborador") or ch,
            "Setor": p.get("setor") or "",
            "Falta ponto": dias_falta_ponto,
            "Justificada SIGRH": dias_just,
            "Sem justificativa": round(gap, 1),
            "Índice %": round((dias_falta_ponto / dias_uteis * 100) if dias_uteis else 0, 2),
        })
    if not out:
        return pd.DataFrame()
    return pd.DataFrame(out).sort_values("Sem justificativa", ascending=False)


funcionarios_rh = carregar_funcionarios_rh()

with st.sidebar:
    st.markdown("### SIGRH")
    st.caption("Painel de gestão")
    menu = st.radio("Módulo", MENU_SIGRH, label_visibility="collapsed")
    st.divider()
    comp_sidebar, _, _ = seletor_competencia("side", mes_default=6, ano_default=2026)
    if st.button("🔄 Atualizar dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Competência: **{comp_sidebar[5:7]}/{comp_sidebar[:4]}**")

col_logo, col_titulo = st.columns([1.1, 5.9])
with col_logo:
    st.markdown(logo_html(118), unsafe_allow_html=True)
with col_titulo:
    st.title("SIGRH")
    st.caption("SANTA VERGÍNIA · GESTÃO DE RECURSOS HUMANOS")
    st.markdown(f'<p style="margin:4px 0 0;font-size:13px;">{link_instagram()}</p>', unsafe_allow_html=True)

st.divider()

if menu == "🏠 Início":
    st.markdown(
        '<div class="ctx-box">'
        '<p style="margin:0;font-size:14px;">👋 Use o <b>menu lateral</b> para navegar entre os módulos '
        '(Justificativas, Absenteísmo, Banco de horas, Folha &amp; encargos, Ponto × Faltas e Demonstrativo RH).</p>'
        '</div>',
        unsafe_allow_html=True,
    )

elif menu == "📋 Justificativas":
    tab_nova, tab_consulta = st.tabs(["📋 Nova justificativa", "🔍 Consultar faltas"])

    with tab_nova:
        st.markdown('<div class="sec">Registrar justificativa de falta</div>', unsafe_allow_html=True)

        if not funcionarios_rh:
            st.warning("Nenhum funcionário cadastrado. Contate o RH.")

        opcoes_colab = [
            f"{f['nome']} — {f.get('setor') or '—'} — {f.get('cargo') or '—'}" for f in funcionarios_rh
        ]

        if opcoes_colab:
            colab_label = st.selectbox("👤 Funcionário", options=opcoes_colab, key="sel_colab")
            nome_sel = colab_label.split(" — ", 1)[0]
            info = funcionario_por_nome(nome_sel, funcionarios_rh) or {}
            setor_default = indice_setor(info.get("setor"))
        else:
            colab_label = ""
            info = {}
            setor_default = 0
            nome_manual = st.text_input("👤 Nome do funcionário", key="nome_manual")

        with st.form("form_falta", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                data_falta = st.date_input("📅 Data da falta", value=date.today(), format="DD/MM/YYYY")
            with c2:
                dias_ausencia = st.number_input("📆 Dias de ausência", min_value=0.5, max_value=30.0, value=1.0, step=0.5)
            with c3:
                possui_atestado = st.checkbox("📎 Possui atestado / declaração")

            c4, c5 = st.columns(2)
            with c4:
                setor = st.selectbox("🏢 Setor", options=SETORES, index=setor_default if opcoes_colab else 0)
            with c5:
                tipo = st.selectbox("📌 Tipo de justificativa", options=TIPOS_JUSTIFICATIVA)

            motivo = st.text_input("📝 Motivo resumido", placeholder="Ex.: Consulta médica, problema familiar")
            observacao = st.text_area("💬 Observação (opcional)", height=68)
            registrado_por = st.text_input("✍️ Registrado por (liderança / RH)", placeholder="Nome de quem registra")

            enviar = st.form_submit_button("✅ Registrar justificativa", type="primary", use_container_width=True)

        if enviar:
            if opcoes_colab:
                nome = nome_sel
                id_rh = info.get("id_rh")
                cargo = info.get("cargo") or ""
            else:
                nome = (nome_manual or "").strip()
                id_rh = None
                cargo = ""
            if not nome:
                st.warning("Informe o colaborador.")
            elif not motivo.strip():
                st.warning("Informe o motivo.")
            else:
                registro = {
                    "data_falta": str(data_falta),
                    "id_rh": id_rh,
                    "id_colaborador": id_rh,
                    "nome_colaborador": nome,
                    "setor": setor,
                    "funcao": cargo or None,
                    "tipo_justificativa": tipo,
                    "dias_ausencia": float(dias_ausencia),
                    "possui_atestado": possui_atestado,
                    "motivo": motivo.strip(),
                    "observacao": observacao.strip() or None,
                    "status": "REGISTRADO",
                    "registrado_por": registrado_por.strip() or None,
                }
                try:
                    sb.table(TABELA).insert(registro).execute()
                    st.success(f"Justificativa registrada — {nome} · {fmt_data(data_falta)} · {dias_ausencia} dia(s)")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    msg = str(e)
                    if "dim_rh" in msg and "does not exist" in msg.lower():
                        st.error("Tabela dim_rh não criada. Rode sql/002_dim_rh.sql no Supabase.")
                    elif "rh_justificativa_faltas" in msg and "does not exist" in msg.lower():
                        st.error("Tabela ainda não criada. Rode o SQL em SIGCF_RH/sql/001_rh_justificativa_faltas.sql no Supabase.")
                    else:
                        st.error(f"Erro ao salvar: {e}")

    with tab_consulta:
        st.markdown('<div class="sec">Consultar justificativas</div>', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        with f1:
            ini = st.date_input("Data início", value=None, key="ci", format="DD/MM/YYYY")
        with f2:
            fim = st.date_input("Data fim", value=None, key="cf", format="DD/MM/YYYY")
        with f3:
            filtro_setor = st.selectbox("Setor", ["Todos"] + SETORES, key="cs")

        rows = carregar_faltas(ini, fim)
        if filtro_setor != "Todos":
            rows = [r for r in rows if (r.get("setor") or "") == filtro_setor]

        if rows:
            df = df_faltas(rows)
            m1, m2, m3 = st.columns(3)
            m1.metric("Registros", len(rows))
            m2.metric("Total dias ausência", f"{sum(float(r.get('dias_ausencia') or 0) for r in rows):.1f}")
            m3.metric("Com atestado", sum(1 for r in rows if r.get("possui_atestado")))
            dark_table(df, height=380)
            st.download_button(
                "⬇️ Exportar Excel",
                data=gerar_excel(df),
                file_name=f"rh_faltas_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("Nenhuma justificativa no período.")

elif menu == "📊 Absenteísmo":
    st.markdown('<div class="sec">Índice de absenteísmo</div>', unsafe_allow_html=True)
    st.caption(
        "Fórmula: (total dias de ausência ÷ colaboradores × dias úteis) × 100. "
        "Com ponto importado, use **Ponto × Faltas** para cruzamento."
    )

    comp_abs, mes, ano = seletor_competencia("abs", mes_default=6, ano_default=2026)
    ac3 = st.number_input("Dias úteis no mês", min_value=1, max_value=31, value=DIAS_UTEIS_MES, key="abs_du")

    ultimo_dia = monthrange(int(ano), int(mes))[1]
    ini_mes = date(int(ano), int(mes), 1)
    fim_mes = date(int(ano), int(mes), ultimo_dia)
    rows_mes = carregar_faltas(ini_mes, fim_mes)
    ponto_mes = carregar_ponto(comp_abs)

    num_colab = len(funcionarios_rh) if funcionarios_rh else st.number_input(
        "Colaboradores ativos (estimativa)", min_value=1, value=50, key="nc_est"
    )
    resumo = calcular_absenteismo(rows_mes, num_colab, int(ac3))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Índice (justificativas)", f"{resumo['indice']:.2f} %")
    m2.metric("Dias ausência", f"{resumo['total_dias']:.1f}")
    m3.metric("Colaboradores", num_colab)
    m4.metric("Período", f"{mes:02d}/{ano}")

    if ponto_mes is not None and ponto_mes:
        total_falta_ponto = sum(float(r.get("dias_falta") or 0) for r in ponto_mes)
        idx_ponto = (total_falta_ponto / (num_colab * int(ac3)) * 100) if num_colab and ac3 else 0
        st.metric("Índice (relatório ponto)", f"{idx_ponto:.2f} %", help="Baseado em rh_ponto_mensal importado")

    st.markdown('<div class="sec">Por colaborador</div>', unsafe_allow_html=True)
    if rows_mes:
        df_m = pd.DataFrame(rows_mes)
        por_pessoa = (
            df_m.groupby("nome_colaborador")
            .agg(Dias=("dias_ausencia", "sum"), Registros=("id", "count"), Setor=("setor", "first"))
            .reset_index()
            .rename(columns={"nome_colaborador": "Colaborador"})
        )
        por_pessoa["Dias"] = por_pessoa["Dias"].astype(float).round(1)
        por_pessoa["Índice %"] = (por_pessoa["Dias"] / float(ac3) * 100).round(2)
        por_pessoa = por_pessoa.sort_values("Dias", ascending=False)
        dark_table(por_pessoa, height=280)

        st.markdown('<div class="sec">Por setor</div>', unsafe_allow_html=True)
        por_setor = (
            df_m.groupby("setor")
            .agg(Dias=("dias_ausencia", "sum"), Registros=("id", "count"))
            .reset_index()
            .rename(columns={"setor": "Setor"})
        )
        por_setor["Dias"] = por_setor["Dias"].astype(float).round(1)
        dark_table(por_setor, height=200)
    else:
        st.info("Sem faltas registradas neste mês — índice zerado.")

elif menu == "⏱️ Banco de horas":
    st.markdown('<div class="sec">Banco de horas — competência</div>', unsafe_allow_html=True)
    comp_banco, _, _ = seletor_competencia("banco", mes_default=6, ano_default=2026)
    rows_banco = carregar_banco_horas(comp_banco)
    rows_setor = carregar_banco_setor(comp_banco)

    if rows_banco is None:
        st.error("Tabela `rh_banco_horas` não encontrada. Rode `sql/003_rh_banco_horas_folha_ponto.sql` no Supabase.")
    else:
        kpi = kpi_banco(rows_banco or [])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Colaboradores", kpi["colab"])
        c2.metric("Qtde HE gerada no mês", f"{kpi['horas_saldo']:.1f} h")
        c3.metric("Saldo acumulado (banco)", f"{kpi['saldo_acumulado_total']:.1f} h")
        c4.metric("Valor total se pago", fmt_moeda(kpi["valor_total"]))

        nomes_rh = {f["id_rh"]: f["nome"] for f in funcionarios_rh}
        cargos_rh = {f["id_rh"]: (f.get("cargo") or "—") for f in funcionarios_rh}

        col_mini, col_rank = st.columns([1, 1.3])
        with col_mini:
            st.markdown('<div class="sec">💼 Saldo do banco por setor</div>', unsafe_allow_html=True)
            if rows_setor:
                pares = sorted(
                    ((r.get("setor") or "—", float(r.get("horas_saldo_total") or 0)) for r in rows_setor),
                    key=lambda p: p[1], reverse=True,
                )
            elif rows_banco:
                acc = {}
                for r in rows_banco:
                    s = r.get("setor") or "—"
                    acc[s] = acc.get(s, 0.0) + float(r.get("saldo_acumulado") or 0)
                pares = sorted(acc.items(), key=lambda p: p[1], reverse=True)
            else:
                pares = []

            if pares:
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
            else:
                st.info("Sem dados de banco de horas nesta competência.")

        with col_rank:
            st.markdown('<div class="sec">🔎 Consulta individual — maior → menor saldo</div>', unsafe_allow_html=True)
            if rows_banco:
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
            else:
                st.info("Sem colaboradores para ranquear nesta competência.")

        st.divider()
        tab_ind, tab_set, tab_lanc = st.tabs(["👤 Individual", "🏢 Por setor (FOPA)", "➕ Lançamento"])

        with tab_ind:
            if rows_banco:
                df_ind = pd.DataFrame(rows_banco)
                nomes = {f["id_rh"]: f["nome"] for f in funcionarios_rh}
                df_ind["Colaborador"] = df_ind["id_rh"].map(nomes).fillna(df_ind["id_rh"])
                cols_show = [
                    "Colaborador", "setor", "horas_he_50", "horas_he_100", "saldo_mes",
                    "saldo_acumulado", "valor_he_50", "valor_he_100", "valor_total",
                ]
                df_show = df_ind[[c for c in cols_show if c in df_ind.columns]].rename(columns={
                    "setor": "Setor", "horas_he_50": "HE 50%", "horas_he_100": "HE 100%",
                    "saldo_mes": "Saldo mês", "saldo_acumulado": "Saldo acum.",
                    "valor_he_50": "R$ HE 50%", "valor_he_100": "R$ HE 100%", "valor_total": "R$ Total",
                })
                dark_table(df_show, height=360)
                st.download_button(
                    "⬇️ Exportar Excel",
                    data=gerar_excel(df_show),
                    file_name=f"banco_horas_{comp_banco[:7]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            else:
                st.info("Nenhum registro individual nesta competência. Lance via aba **Lançamento** ou importe FOPA.")

        with tab_set:
            st.caption("Resumo FOPA agregado por setor (Saldo FOPA 06/2026 e demais meses).")
            if rows_setor:
                df_s = pd.DataFrame(rows_setor).rename(columns={
                    "setor": "Setor", "qtd_colaboradores": "Qtd", "horas_he_50": "HE 50%",
                    "horas_he_100": "HE 100%", "horas_saldo_total": "Saldo (h)", "valor_total": "R$ Total",
                })
                dark_table(df_s[["Setor", "Qtd", "HE 50%", "HE 100%", "Saldo (h)", "R$ Total"]], height=280)
            elif rows_banco:
                df_agg = df_banco_por_setor(rows_banco)
                st.caption("Calculado a partir dos registros individuais (FOPA setor ainda não importado).")
                dark_table(df_agg, height=280)
            else:
                st.info("Importe saldo FOPA por setor ou lance registros individuais.")

        with tab_lanc:
            st.markdown('<div class="sec">Lançamento manual</div>', unsafe_allow_html=True)
            opcoes_colab = [
                f"{f['nome']} — {f.get('setor') or '—'}" for f in funcionarios_rh
            ]
            if not opcoes_colab:
                st.warning("Cadastre colaboradores em dim_rh primeiro.")
            else:
                with st.form("form_banco"):
                    colab_b = st.selectbox("Colaborador", opcoes_colab)
                    nome_b = colab_b.split(" — ", 1)[0]
                    info_b = funcionario_por_nome(nome_b, funcionarios_rh) or {}
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        he50 = st.number_input("HE 50% (h)", min_value=0.0, step=0.5, value=0.0)
                    with bc2:
                        he100 = st.number_input("HE 100% (h)", min_value=0.0, step=0.5, value=0.0)
                    with bc3:
                        saldo_m = st.number_input("Saldo mês (h)", step=0.5, value=0.0)
                    bv1, bv2, bv3 = st.columns(3)
                    with bv1:
                        v50 = st.number_input("R$ HE 50%", min_value=0.0, step=0.01, value=0.0)
                    with bv2:
                        v100 = st.number_input("R$ HE 100%", min_value=0.0, step=0.01, value=0.0)
                    with bv3:
                        vtot = st.number_input("R$ Total", min_value=0.0, step=0.01, value=0.0)
                    salvar_b = st.form_submit_button("Salvar banco de horas", type="primary", use_container_width=True)
                if salvar_b and info_b.get("id_rh"):
                    reg = {
                        "id_rh": info_b["id_rh"],
                        "competencia": comp_banco,
                        "setor": info_b.get("setor"),
                        "horas_he_50": he50,
                        "horas_he_100": he100,
                        "saldo_mes": saldo_m,
                        "valor_he_50": v50,
                        "valor_he_100": v100,
                        "valor_total": vtot or (v50 + v100),
                        "origem": "MANUAL",
                    }
                    try:
                        sb.table(T_BANCO).upsert(reg, on_conflict="id_rh,competencia").execute()
                        st.success("Registro salvo.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

elif menu == "💰 Folha & encargos":
    st.markdown('<div class="sec">Folha mensal — bruto, encargos e líquido</div>', unsafe_allow_html=True)
    comp_folha, _, _ = seletor_competencia("folha", mes_default=6, ano_default=2026)
    rows_folha = carregar_folha(comp_folha)

    if rows_folha is None:
        st.error("Tabela `rh_folha_mensal` não encontrada. Rode `sql/003_rh_banco_horas_folha_ponto.sql` no Supabase.")
    else:
        tot_bruto = sum(float(r.get("salario_bruto") or 0) for r in (rows_folha or []))
        tot_enc = sum(float(r.get("encargos_empresa") or 0) for r in (rows_folha or []))
        tot_liq = sum(float(r.get("salario_liquido") or 0) for r in (rows_folha or []))
        tot_desc = sum(float(r.get("descontos") or 0) for r in (rows_folha or []))
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Bruto total", fmt_moeda(tot_bruto))
        f2.metric("Encargos empresa", fmt_moeda(tot_enc))
        f3.metric("Descontos", fmt_moeda(tot_desc))
        f4.metric("Líquido total", fmt_moeda(tot_liq))

        tab_folha, tab_f_lanc = st.tabs(["📋 Colaboradores", "➕ Lançamento"])

        with tab_folha:
            if rows_folha:
                df_f = pd.DataFrame(rows_folha)
                nomes = {f["id_rh"]: f["nome"] for f in funcionarios_rh}
                df_f["Colaborador"] = df_f["id_rh"].map(nomes).fillna(df_f["id_rh"])
                df_show = df_f[[
                    "Colaborador", "setor", "cargo", "salario_bruto", "encargos_empresa",
                    "descontos", "salario_liquido", "valor_hora_ref",
                ]].rename(columns={
                    "setor": "Setor", "cargo": "Cargo", "salario_bruto": "Bruto",
                    "encargos_empresa": "Encargos", "descontos": "Descontos",
                    "salario_liquido": "Líquido", "valor_hora_ref": "R$/h ref.",
                })
                dark_table(df_show, height=360)
            else:
                st.info("Nenhum registro de folha nesta competência.")

        with tab_f_lanc:
            opcoes_colab = [f"{f['nome']} — {f.get('setor') or '—'}" for f in funcionarios_rh]
            if opcoes_colab:
                with st.form("form_folha"):
                    colab_f = st.selectbox("Colaborador", opcoes_colab, key="folha_colab")
                    nome_f = colab_f.split(" — ", 1)[0]
                    info_f = funcionario_por_nome(nome_f, funcionarios_rh) or {}
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        bruto = st.number_input("Salário bruto", min_value=0.0, step=0.01, value=0.0)
                        encargos = st.number_input("Encargos empresa", min_value=0.0, step=0.01, value=0.0)
                    with fc2:
                        descontos = st.number_input("Descontos", min_value=0.0, step=0.01, value=0.0)
                        liquido = st.number_input("Salário líquido", min_value=0.0, step=0.01, value=0.0)
                    vhora = st.number_input("Valor hora ref. (R$)", min_value=0.0, step=0.01, value=0.0)
                    salvar_f = st.form_submit_button("Salvar folha", type="primary", use_container_width=True)
                if salvar_f and info_f.get("id_rh"):
                    reg = {
                        "id_rh": info_f["id_rh"],
                        "competencia": comp_folha,
                        "setor": info_f.get("setor"),
                        "cargo": info_f.get("cargo"),
                        "salario_bruto": bruto,
                        "encargos_empresa": encargos,
                        "descontos": descontos,
                        "salario_liquido": liquido or max(bruto - descontos, 0),
                        "valor_hora_ref": vhora or None,
                        "origem": "MANUAL",
                    }
                    try:
                        sb.table(T_FOLHA).upsert(reg, on_conflict="id_rh,competencia").execute()
                        st.success("Folha salva.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

elif menu == "🕐 Ponto × Faltas":
    st.markdown('<div class="sec">Relatório de ponto × justificativas SIGRH</div>', unsafe_allow_html=True)
    st.caption(
        "Base para absenteísmo: faltas do **relatório de ponto** cruzadas com **justificativas** "
        "registradas no SIGRH (sistema anterior até migração completa)."
    )
    comp_ponto, mes_p, ano_p = seletor_competencia("ponto", mes_default=6, ano_default=2026)
    rows_ponto = carregar_ponto(comp_ponto)

    ultimo_dia = monthrange(int(ano_p), int(mes_p))[1]
    ini_mes = date(int(ano_p), int(mes_p), 1)
    fim_mes = date(int(ano_p), int(mes_p), ultimo_dia)
    rows_faltas_mes = carregar_faltas(ini_mes, fim_mes)

    if rows_ponto is None:
        st.error("Tabela `rh_ponto_mensal` não encontrada. Rode `sql/003_rh_banco_horas_folha_ponto.sql` no Supabase.")
    elif not rows_ponto:
        st.warning("Nenhum dado de ponto importado para esta competência.")
        st.info(
            "Enquanto isso, o índice de absenteísmo usa apenas as **justificativas** cadastradas em "
            "📋 Justificativas / 📊 Absenteísmo."
        )
        if rows_faltas_mes:
            resumo = calcular_absenteismo(
                rows_faltas_mes,
                len(funcionarios_rh) or 50,
                DIAS_UTEIS_MES,
            )
            st.metric("Índice provisório (só justificativas)", f"{resumo['indice']:.2f} %")
    else:
        dias_uteis_p = int(rows_ponto[0].get("dias_uteis") or DIAS_UTEIS_MES)
        df_cruz = cruzar_ponto_faltas(rows_ponto, rows_faltas_mes or [], dias_uteis_p)
        total_falta = sum(float(r.get("dias_falta") or 0) for r in rows_ponto)
        total_sem_just = df_cruz["Sem justificativa"].sum() if not df_cruz.empty else 0
        num_colab = len(rows_ponto)
        idx_ponto = (total_falta / (num_colab * dias_uteis_p) * 100) if num_colab and dias_uteis_p else 0
        idx_gap = (total_sem_just / (num_colab * dias_uteis_p) * 100) if num_colab and dias_uteis_p else 0

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Colaboradores (ponto)", num_colab)
        p2.metric("Dias falta (ponto)", f"{total_falta:.1f}")
        p3.metric("Índice absenteísmo", f"{idx_ponto:.2f} %")
        p4.metric("Sem justificativa", f"{total_sem_just:.1f} d · {idx_gap:.2f} %")

        dark_table(df_cruz, height=400)
        st.download_button(
            "⬇️ Exportar cruzamento",
            data=gerar_excel(df_cruz),
            file_name=f"ponto_faltas_{comp_ponto[:7]}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with st.expander("➕ Importar resumo de ponto (manual)"):
            opcoes_colab = [f"{f['nome']} — {f.get('setor') or '—'}" for f in funcionarios_rh]
            if opcoes_colab:
                with st.form("form_ponto"):
                    colab_p = st.selectbox("Colaborador", opcoes_colab)
                    nome_p = colab_p.split(" — ", 1)[0]
                    info_p = funcionario_por_nome(nome_p, funcionarios_rh) or {}
                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        du = st.number_input("Dias úteis", min_value=1, max_value=31, value=DIAS_UTEIS_MES)
                        dt = st.number_input("Dias trabalhados", min_value=0.0, step=0.5, value=0.0)
                    with pc2:
                        dfalta = st.number_input("Dias falta", min_value=0.0, step=0.5, value=0.0)
                        djust = st.number_input("Faltas injustificadas", min_value=0.0, step=0.5, value=0.0)
                    with pc3:
                        hr_prev = st.number_input("Horas previstas", min_value=0.0, step=0.5, value=0.0)
                        hr_real = st.number_input("Horas realizadas", min_value=0.0, step=0.5, value=0.0)
                    salvar_p = st.form_submit_button("Salvar ponto", type="primary", use_container_width=True)
                if salvar_p and info_p.get("id_rh"):
                    reg = {
                        "id_rh": info_p["id_rh"],
                        "competencia": comp_ponto,
                        "nome_colaborador": info_p.get("nome"),
                        "setor": info_p.get("setor"),
                        "dias_uteis": int(du),
                        "dias_trabalhados": dt,
                        "dias_falta": dfalta,
                        "faltas_injustificadas": djust,
                        "horas_previstas": hr_prev,
                        "horas_realizadas": hr_real,
                        "origem": "MANUAL",
                    }
                    try:
                        sb.table(T_PONTO).upsert(reg, on_conflict="id_rh,competencia").execute()
                        st.success("Ponto salvo.")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

elif menu == "📈 Demonstrativo RH":
    st.markdown('<div class="sec">Demonstrativo — horas × valor hora (folha)</div>', unsafe_allow_html=True)
    comp_dem, _, _ = seletor_competencia("dem", mes_default=6, ano_default=2026)
    rows_banco = carregar_banco_horas(comp_dem) or []
    rows_folha = carregar_folha(comp_dem) or []

    if not rows_banco and not rows_folha:
        st.info("Lance banco de horas e folha para gerar o demonstrativo.")
    else:
        folha_por_rh = {r["id_rh"]: r for r in rows_folha}
        nomes = {f["id_rh"]: f["nome"] for f in funcionarios_rh}
        linhas = []
        for b in rows_banco:
            id_rh = b.get("id_rh")
            f = folha_por_rh.get(id_rh, {})
            vh = float(f.get("valor_hora_ref") or 0)
            saldo_h = float(b.get("saldo_mes") or 0)
            linhas.append({
                "Colaborador": nomes.get(id_rh, id_rh),
                "Setor": b.get("setor") or f.get("setor") or "",
                "Saldo (h)": round(saldo_h, 1),
                "R$/h ref.": round(vh, 2),
                "Valor ref. saldo": round(saldo_h * vh, 2),
                "R$ HE registrado": round(float(b.get("valor_total") or 0), 2),
                "Bruto folha": round(float(f.get("salario_bruto") or 0), 2),
                "Líquido folha": round(float(f.get("salario_liquido") or 0), 2),
            })
        df_dem = pd.DataFrame(linhas)
        if not df_dem.empty:
            d1, d2, d3 = st.columns(3)
            d1.metric("Saldo horas total", f"{df_dem['Saldo (h)'].sum():.1f} h")
            d2.metric("Valor ref. saldo", fmt_moeda(df_dem["Valor ref. saldo"].sum()))
            d3.metric("R$ HE registrado", fmt_moeda(df_dem["R$ HE registrado"].sum()))

            st.markdown('<div class="sec">Por setor</div>', unsafe_allow_html=True)
            por_setor = (
                df_dem.groupby("Setor")
                .agg({"Saldo (h)": "sum", "Valor ref. saldo": "sum", "R$ HE registrado": "sum", "Colaborador": "count"})
                .rename(columns={"Colaborador": "Qtd"})
                .reset_index()
            )
            dark_table(por_setor, height=200)

            st.markdown('<div class="sec">Individual</div>', unsafe_allow_html=True)
            dark_table(df_dem.sort_values("Saldo (h)", ascending=False), height=360)

st.divider()
st.markdown(
    f'<p style="text-align:center;font-size:12px;color:#8aab80;margin:0;">'
    f'SIGRH · SANTA VERGÍNIA · '
    f'{link_instagram("Instagram")}'
    f'</p>',
    unsafe_allow_html=True,
)
