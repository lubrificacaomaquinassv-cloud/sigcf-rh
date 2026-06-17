"""PIN opcional SIGRH / SIGCF."""
import streamlit as st

LOGO_URL = "https://i.postimg.cc/Y9X7ddnb/LOGO-BP.jpg"
BG_URL = "https://media.bio.site/sites/32a25c2c-d6fa-4dfc-bdc2-27e4d35d7ea2/AhS9mKiQxFRXAyMBdXDzEG.jpg"
INSTAGRAM_URL = "https://www.instagram.com/fazendasantaverginia"
SESSION_KEY = "sigcf_auth"

INSTA_ICON = (
    '<svg class="insta-ico" viewBox="0 0 24 24" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
    '<path fill="currentColor" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>'
    "</svg>"
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
