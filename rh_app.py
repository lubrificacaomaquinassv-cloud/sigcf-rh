import streamlit as st
from datetime import date, datetime
from supabase import create_client, Client
from sigcf_auth import exigir_acesso, logo_html

st.set_page_config(
    page_title="SIGRH — SANTA VERGÍNIA",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
TABELA = "rh_justificativa_faltas"
TABELA_FEEDBACK = "rh_feedback_lideranca"


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

TIPOS_FEEDBACK = [
    "Elogio / reconhecimento",
    "Sugestão de melhoria",
    "Reclamação / insatisfação",
    "Denúncia / conduta",
    "Solicitação de apoio RH",
    "Outros",
]

OPCOES_REGISTRO_FEEDBACK = [
    "Registrar feedback positivo",
    "Registrar ponto de atenção",
    "Registrar solicitação de ação",
    "Registrar encerramento / follow-up",
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
    {"id": "feedback", "nome": "Feedback da liderança", "icone": "💬", "ativo": True},
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
.logo-frame{background:linear-gradient(145deg,#0a1628,#0d2040);border:2px solid #c9a227;
 border-radius:12px;padding:5px;display:inline-block;box-shadow:0 4px 18px rgba(0,0,0,.45);}
.logo-frame img{display:block;border-radius:8px;}
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
.stTabs [data-baseweb="tab-list"]{background:rgba(13,24,12,0.88);border-bottom:1px solid #2a3d28;gap:8px;}
.stTabs [data-baseweb="tab"]{
 color:#9ab892!important;font-family:'Barlow Condensed',sans-serif;font-weight:600;}
.stTabs [aria-selected="true"]{color:#e8edd0!important;border-bottom-color:#5a9452!important;}
.stTabs [data-baseweb="tab-highlight"]{background-color:#5a9452!important;}
div[data-testid="stCheckbox"] label span{color:#e8edd0!important;}
div[data-testid="stRadio"] label span{color:#e8edd0!important;}
.stButton button,[data-testid="stFormSubmitButton"] button{
 background:#4a9e3f!important;color:#ffffff!important;border:1px solid #6fa864!important;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:1.5px;
 text-transform:uppercase;border-radius:8px;min-height:44px;}
.stButton button:hover,[data-testid="stFormSubmitButton"] button:hover{background:#3d8534!important;}
.feedback-intro{color:#9ab892;font-size:14px;line-height:1.55;margin:0 0 14px;}

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


def indice_setor(setor: str) -> int:
    s = (setor or "Outros").strip()
    if s in SETORES:
        return SETORES.index(s)
    return SETORES.index("Outros")


def label_colaborador(info: dict) -> str:
    return f"{info['nome']} — {info.get('setor') or '—'} — {info.get('cargo') or '—'}"


def carregar_lideres(lista: list) -> list:
    chaves = ("chefe", "líder", "lider", "gerente", "coordenador", "supervisor", "encarregado")
    lideres = [
        f for f in lista
        if any(k in (f.get("cargo") or "").lower() for k in chaves)
    ]
    return lideres or lista


funcionarios_rh = carregar_funcionarios_rh()
opcoes_colab = [label_colaborador(f) for f in funcionarios_rh]
opcoes_lider = [label_colaborador(f) for f in carregar_lideres(funcionarios_rh)]

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

tab_justificativa, tab_feedback = st.tabs([
    "📋 Nova justificativa",
    "💬 Feedback da liderança",
])

with tab_justificativa:
    st.markdown('<div class="sec">Registrar justificativa de falta</div>', unsafe_allow_html=True)

    if not funcionarios_rh:
        st.warning("Nenhum funcionário cadastrado. Contate o RH.")

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
                    st.error("Tabela ainda não criada. Rode sql/001_rh_justificativa_faltas.sql no Supabase.")
                else:
                    st.error(f"Erro ao salvar: {e}")

with tab_feedback:
    st.markdown('<div class="sec">Feedback da liderança</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="feedback-intro">Preencha o formulário de feedback da liderança e nos ajude a '
        "identificar e melhorar os pontos críticos da empresa. Cada resposta é uma peça importante "
        "para que possamos crescer juntos e criar um ambiente cada vez melhor para trabalhar.</p>",
        unsafe_allow_html=True,
    )

    if not funcionarios_rh:
        st.warning("Nenhum colaborador cadastrado. Contate o RH.")

    with st.form("form_feedback", clear_on_submit=True):
        responsavel = st.radio(
            "Responsável pelo feedback *",
            options=["RH", "Líder", "Direção", "Encerramento"],
            horizontal=True,
        )

        if opcoes_lider:
            lider_label = st.selectbox(
                "Nome do líder do setor *",
                options=opcoes_lider,
                index=None,
                placeholder="Escolha uma opção",
            )
        else:
            lider_label = st.text_input("Nome do líder do setor *", placeholder="Nome completo")

        if opcoes_colab:
            referente_label = st.selectbox(
                "Referente de realimentação *",
                options=opcoes_colab,
                index=None,
                placeholder="Escolha uma opção",
            )
        else:
            referente_label = st.text_input("Referente de realimentação *", placeholder="Nome completo")

        setor_fb = st.selectbox(
            "Insira o setor de trabalho da equipe ou do colaborador",
            options=SETORES,
            index=None,
            placeholder="Escolha uma opção",
        )

        tipo_fb = st.selectbox(
            "Qual o tipo desse feedback *",
            options=TIPOS_FEEDBACK,
            index=None,
            placeholder="Escolha uma opção",
        )

        opcao_registro = st.selectbox(
            "Qual das opções abaixo gostaria de registrar agora *",
            options=OPCOES_REGISTRO_FEEDBACK,
            index=None,
            placeholder="Escolha uma opção",
        )

        descricao = st.text_area(
            "Descreva abaixo o máximo de detalhes possíveis sobre o seu feedback *",
            placeholder="Digite aqui ...",
            height=120,
        )

        visita_rh = st.radio(
            "Você acredita ser necessária visita no local do gestor de RH?",
            options=["Sim", "Não", "Talvez"],
            horizontal=True,
        )

        enviar_fb = st.form_submit_button("✅ Registrar feedback", type="primary", use_container_width=True)

    if enviar_fb:
        lider = (lider_label.split(" — ", 1)[0] if opcoes_lider else (lider_label or "").strip())
        referente = (
            referente_label.split(" — ", 1)[0] if opcoes_colab else (referente_label or "").strip()
        )

        if not lider:
            st.warning("Informe o líder do setor.")
        elif not referente:
            st.warning("Informe o referente de realimentação.")
        elif not tipo_fb:
            st.warning("Selecione o tipo de feedback.")
        elif not opcao_registro:
            st.warning("Selecione a opção de registro.")
        elif not descricao.strip():
            st.warning("Descreva o feedback.")
        else:
            registro = {
                "responsavel": responsavel,
                "nome_lider_setor": lider,
                "referente": referente,
                "setor": setor_fb,
                "tipo_feedback": tipo_fb,
                "opcao_registro": opcao_registro,
                "descricao": descricao.strip(),
                "visita_rh": visita_rh,
            }
            try:
                sb.table(TABELA_FEEDBACK).insert(registro).execute()
                st.success(f"Feedback registrado — {referente} · {tipo_fb}")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                msg = str(e)
                if "rh_feedback_lideranca" in msg and "does not exist" in msg.lower():
                    st.error("Tabela ainda não criada. Rode sql/011_rh_feedback_lideranca.sql no Supabase.")
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
