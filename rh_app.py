import streamlit as st
from datetime import date, datetime
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

MODULOS_RH = [
    {"id": "faltas", "nome": "Justificativa de faltas", "icone": "📋", "ativo": True},
    {"id": "absenteismo", "nome": "Índice de absenteísmo", "icone": "📊", "ativo": False},
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
[data-testid="stSidebar"]{
 background:rgba(13,24,12,0.95)!important;border-right:1px solid #2a3d28!important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label{color:#e8edd0!important;}
[data-testid="stSidebar"] .sidebar-desc{color:#9ab892!important;font-size:14px;line-height:1.55;margin-top:8px;}
[data-testid="stHeader"]{background:rgba(10,20,9,0.45)!important;}
.block-container{background:transparent!important;max-width:1100px!important;}
[data-testid="stForm"]{
 background:rgba(255,255,255,0.96)!important;border:1px solid #d8e0d4!important;
 border-radius:14px;padding:24px 28px!important;box-shadow:0 4px 24px rgba(0,0,0,0.25);}
[data-testid="stForm"] label,[data-testid="stForm"] p,[data-testid="stForm"] span{color:#1a2818!important;}
[data-testid="stForm"] .stCaption{color:#4a6644!important;}
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
div[data-testid="stMetric"]{background:rgba(13,24,12,0.88);border:1px solid #2a3d28;border-radius:10px;padding:10px 14px;}
div[data-testid="stMetric"] label{color:#9ab892!important;}
div[data-testid="stMetricValue"]{color:#8ec486!important;font-family:'Barlow Condensed',sans-serif;}
div[data-testid="stRadio"] label span{color:#1a2818!important;}
[data-testid="stForm"] div[data-testid="stCheckbox"] label span,
[data-testid="stForm"] div[data-testid="stRadio"] label span{color:#1a2818!important;}
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


def funcionario_por_nome(nome: str, lista: list) -> dict | None:
    for c in lista:
        if c.get("nome") == nome:
            return c
    return None


funcionarios_rh = carregar_funcionarios_rh()

col_logo, col_titulo, col_acao = st.columns([1.1, 4.9, 1])
with col_logo:
    st.markdown(logo_html(118), unsafe_allow_html=True)
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

with st.sidebar:
    st.markdown(logo_html(140), unsafe_allow_html=True)
    st.markdown("### Justificativa de Falta")
    st.markdown(
        '<p class="sidebar-desc">Preencha o formulário para registrar a justificativa '
        "de ausência do colaborador. Suas informações ajudam o RH a acompanhar faltas "
        "e manter o índice de absenteísmo atualizado.</p>",
        unsafe_allow_html=True,
    )

st.markdown('<div class="sec">Justificativa de Falta</div>', unsafe_allow_html=True)

if not funcionarios_rh:
    st.warning("Nenhum funcionário cadastrado. Contate o RH.")

opcoes_colab = [
    f"{f['nome']} — {f.get('setor') or '—'} — {f.get('cargo') or '—'}" for f in funcionarios_rh
]

with st.form("form_falta", clear_on_submit=True):
    registrado_tipo = st.radio(
        "Registrado por *",
        options=["RH", "Líder", "Direção"],
        horizontal=True,
    )

    if opcoes_colab:
        colab_label = st.selectbox(
            "Colaborador *",
            options=opcoes_colab,
            index=None,
            placeholder="Escolha uma opção",
        )
    else:
        nome_manual = st.text_input("Colaborador *", placeholder="Nome completo do colaborador")

    c1, c2 = st.columns(2)
    with c1:
        data_falta = st.date_input("Data da falta *", value=date.today(), format="DD/MM/YYYY")
    with c2:
        dias_ausencia = st.number_input(
            "Dias de ausência *", min_value=0.5, max_value=30.0, value=1.0, step=0.5
        )

    setor = st.selectbox(
        "Setor de trabalho da equipe ou do colaborador",
        options=SETORES,
        index=0,
    )

    tipo = st.selectbox(
        "Tipo de justificativa *",
        options=TIPOS_JUSTIFICATIVA,
        index=None,
        placeholder="Escolha uma opção",
    )

    possui_atestado = st.radio(
        "Possui atestado ou declaração? *",
        options=["Sim", "Não"],
        horizontal=True,
    )

    motivo = st.text_input(
        "Motivo resumido *",
        placeholder="Ex.: Consulta médica, problema familiar",
    )

    observacao = st.text_area(
        "Descreva abaixo o máximo de detalhes possíveis sobre a justificativa",
        placeholder="Digite aqui ...",
        height=120,
    )

    registrado_nome = st.text_input(
        "Nome de quem registra *",
        placeholder="Nome completo",
    )

    enviar = st.form_submit_button("Registrar justificativa", type="primary", use_container_width=True)

if enviar:
    nome = ""
    id_rh = None
    cargo = ""

    if opcoes_colab:
        if not colab_label:
            st.warning("Selecione o colaborador.")
            st.stop()
        nome_sel = colab_label.split(" — ", 1)[0]
        info = funcionario_por_nome(nome_sel, funcionarios_rh) or {}
        nome = nome_sel
        id_rh = info.get("id_rh")
        cargo = info.get("cargo") or ""
        if info.get("setor") in SETORES:
            setor = info.get("setor")
    else:
        nome = (nome_manual or "").strip()
        if not nome:
            st.warning("Informe o colaborador.")
            st.stop()

    if not tipo:
        st.warning("Selecione o tipo de justificativa.")
    elif not motivo.strip():
        st.warning("Informe o motivo.")
    elif not registrado_nome.strip():
        st.warning("Informe o nome de quem registra.")
    else:
        registrado_por = f"{registrado_tipo} — {registrado_nome.strip()}"
        registro = {
            "data_falta": str(data_falta),
            "id_rh": id_rh,
            "id_colaborador": id_rh,
            "nome_colaborador": nome,
            "setor": setor,
            "funcao": cargo or None,
            "tipo_justificativa": tipo,
            "dias_ausencia": float(dias_ausencia),
            "possui_atestado": possui_atestado == "Sim",
            "motivo": motivo.strip(),
            "observacao": observacao.strip() or None,
            "status": "REGISTRADO",
            "registrado_por": registrado_por,
        }
        try:
            sb.table(TABELA).insert(registro).execute()
            st.success(
                f"Justificativa registrada — {nome} · {fmt_data(data_falta)} · {dias_ausencia} dia(s)"
            )
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            msg = str(e)
            if "dim_rh" in msg and "does not exist" in msg.lower():
                st.error("Tabela dim_rh não criada. Rode sql/002_dim_rh.sql no Supabase.")
            elif "rh_justificativa_faltas" in msg and "does not exist" in msg.lower():
                st.error(
                    "Tabela ainda não criada. Rode o SQL em "
                    "SIGCF_RH/sql/001_rh_justificativa_faltas.sql no Supabase."
                )
            else:
                st.error(f"Erro ao salvar: {e}")

st.divider()
st.markdown(
    f'<p style="text-align:center;font-size:12px;color:#8aab80;margin:0;">'
    f'SIGRH · SANTA VERGÍNIA · '
    f'{link_instagram("Instagram")}'
    f'</p>',
    unsafe_allow_html=True,
)
