"""PIN opcional SIGRH / SIGCF."""
import streamlit as st

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
INSTAGRAM_URL = "https://www.instagram.com/fazendasantaverginia"
SESSION_KEY = "sigcf_auth"

INSTA_ICON = (
    '<img class="insta-ico" src="https://cdn.simpleicons.org/instagram/8ec486" '
    'width="17" height="17" alt="" loading="lazy">'
)


def link_instagram(text: str = "@fazendasantaverginia") -> str:
    return (
        f'<a class="insta-link" href="{INSTAGRAM_URL}" target="_blank" rel="noopener">'
        f"{INSTA_ICON}{text}</a>"
    )


def exigir_acesso(titulo: str, subtitulo: str = "Acesso restrito — SIGRH Santa Virgínia"):
    pin_cfg = str(st.secrets.get("APP_PIN", "") or "").strip()
    if not pin_cfg:
        return
    if st.session_state.get(SESSION_KEY):
        return

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&display=swap');
        .stApp{
         background:linear-gradient(rgba(10,20,9,0.82),rgba(10,20,9,0.92)),
         url('__BG__') center center/cover no-repeat fixed!important;}
        [data-testid="stAppViewContainer"]{background:transparent!important;}
        h1,h2,p,label{color:#e8edd0;}
        h1{font-family:'Barlow Condensed',sans-serif;}
        .logo-box{background:#fff;border-radius:10px;padding:8px 12px;display:inline-block;}
        .insta-link{display:inline-flex;align-items:center;gap:6px;color:#8ec486!important;
         text-decoration:none;font-weight:600;}
        .insta-link:hover{color:#a8d8a0!important;text-decoration:none;}
        .insta-ico{width:17px;height:17px;flex-shrink:0;}
        </style>
        """.replace("__BG__", BG_URL),
        unsafe_allow_html=True,
    )
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.markdown(f'<div class="logo-box"><img src="{LOGO_URL}" width="100"></div>', unsafe_allow_html=True)
    with col_titulo:
        st.title(titulo)
        st.caption(subtitulo)
        st.markdown(
            f'<p style="margin:4px 0 0;font-size:13px;">{link_instagram()}</p>',
            unsafe_allow_html=True,
        )

    pin = st.text_input("PIN de acesso", type="password", key="sigcf_login_pin")
    if st.button("Entrar", type="primary", key="sigcf_login_btn"):
        if pin == pin_cfg:
            st.session_state[SESSION_KEY] = True
            st.rerun()
        else:
            st.error("PIN incorreto.")
    st.stop()
