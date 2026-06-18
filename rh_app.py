import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from calendar import monthrange
from supabase import create_client, Client
from sigcf_auth import exigir_acesso

st.set_page_config(
    page_title="SIGRH — SANTA VERGÍNIA",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
INSTAGRAM_URL = "https://www.instagram.com/fazendasantaverginia"
TABELA = "rh_justificativa_faltas"
DIAS_UTEIS_MES = 22


def link_instagram(text: str = "@fazendasantaverginia") -> str:
    icon = (
        '<img class="insta-ico" src="https://cdn.simpleicons.org/instagram/8ec486" '
        'width="17" height="17" alt="" loading="lazy">'
    )
    return (
        f'<a class="insta-link" href="{INSTAGRAM_URL}" target="_blank" rel="noopener">'
        f"{icon}{text}</a>"
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

MODULOS_RH = [
    {"id": "faltas", "nome": "Justificativa de faltas", "icone": "📋", "ativo": True},
    {"id": "absenteismo", "nome": "Índice de absenteísmo", "icone": "📊", "ativo": True},
    {"id": "contratacao", "nome": "Solicitação de contratação", "icone": "➕", "ativo": False},
    {"id": "demissao", "nome": "Solicitação de demissão", "icone": "📤", "ativo": False},
    {"id": "feedback", "nome": "Feedback da liderança", "icone": "💬", "ativo": False},
]

exigir_acesso("SIGRH — SANTA VERGÍNIA")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
.stApp{
 background:linear-gradient(rgba(10,20,9,0.68),rgba(10,20,9,0.82)),
 url('__BG__') center center/cover no-repeat fixed!important;}
[data-testid="stAppViewContainer"]{background:transparent!important;}
[data-testid="stSidebar"]{display:none;}
[data-testid="stHeader"]{background:rgba(10,20,9,0.45)!important;}
.block-container{background:transparent!important;max-width:980px!important;}
h1,h2,h3,h4,p,span,label{color:#e8edd0;}
h1{font-family:'Barlow Condensed',sans-serif;letter-spacing:1px;}
.stCaption,[data-testid="stCaptionContainer"] p{color:#9ab892!important;}
.sec{font-family:'Barlow Condensed',sans-serif;font-size:12px;font-weight:700;
 letter-spacing:2px;text-transform:uppercase;color:#9ab892;
 border-left:4px solid #5a9452;padding-left:10px;margin:8px 0 12px;}
.logo-box{background:#ffffff;border-radius:10px;padding:8px 12px;display:inline-block;}
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


funcionarios_rh = carregar_funcionarios_rh()

col_logo, col_titulo, col_acao = st.columns([1, 5, 1])
with col_logo:
    st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="100"></div>', unsafe_allow_html=True)
with col_titulo:
    st.title("SIGRH")
    st.caption("SANTA VERGÍNIA · GESTÃO DE RECURSOS HUMANOS")
    st.markdown(
        f'<p style="margin:4px 0 0;font-size:13px;">{link_instagram()}</p>',
        unsafe_allow_html=True,
    )
with col_acao:
    if st.button("🔄 Atualizar"):
        st.cache_data.clear()
        st.rerun()

st.divider()

st.markdown('<div class="sec">Módulos SIGRH</div>', unsafe_allow_html=True)
cols = st.columns(len(MODULOS_RH))
for i, mod in enumerate(MODULOS_RH):
    cls = "active" if mod["ativo"] else "soon"
    tag = "DISPONÍVEL" if mod["ativo"] else "EM BREVE"
    with cols[i]:
        st.markdown(
            f'<div class="hub-card {cls}">'
            f'<div class="ico">{mod["icone"]}</div>'
            f'<div class="tit">{mod["nome"]}</div>'
            f'<span class="tag">{tag}</span></div>',
            unsafe_allow_html=True,
        )

st.divider()

tab_nova, tab_consulta, tab_abs = st.tabs([
    "📋 Nova justificativa",
    "🔍 Consultar faltas",
    "📊 Índice de absenteísmo",
])

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

with tab_abs:
    st.markdown('<div class="sec">Índice de absenteísmo</div>', unsafe_allow_html=True)
    st.caption(
        f"Fórmula: (total dias de ausência ÷ colaboradores × {DIAS_UTEIS_MES} dias úteis) × 100. "
        "Ajuste conforme política RH."
    )

    hoje = date.today()
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        mes = st.selectbox("Mês", list(range(1, 13)), index=hoje.month - 1)
    with ac2:
        ano = st.number_input("Ano", min_value=2024, max_value=2030, value=hoje.year, step=1)
    with ac3:
        dias_uteis = st.number_input("Dias úteis no mês", min_value=1, max_value=31, value=DIAS_UTEIS_MES)

    ultimo_dia = monthrange(int(ano), int(mes))[1]
    ini_mes = date(int(ano), int(mes), 1)
    fim_mes = date(int(ano), int(mes), ultimo_dia)
    rows_mes = carregar_faltas(ini_mes, fim_mes)

    num_colab = len(funcionarios_rh) if funcionarios_rh else st.number_input(
        "Colaboradores ativos (estimativa)", min_value=1, value=50, key="nc_est"
    )
    resumo = calcular_absenteismo(rows_mes, num_colab, int(dias_uteis))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Índice do mês", f"{resumo['indice']:.2f} %")
    m2.metric("Dias ausência", f"{resumo['total_dias']:.1f}")
    m3.metric("Colaboradores", num_colab)
    m4.metric("Período", f"{mes:02d}/{ano}")

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
        por_pessoa["Índice %"] = (por_pessoa["Dias"] / float(dias_uteis) * 100).round(2)
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

st.divider()
st.markdown(
    f'<p style="text-align:center;font-size:12px;color:#8aab80;margin:0;">'
    f'SIGRH · Santa Virgínia · '
    f'{link_instagram("Instagram")}'
    f'</p>',
    unsafe_allow_html=True,
)
