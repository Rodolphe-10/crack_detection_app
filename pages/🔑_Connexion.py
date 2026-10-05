#!/usr/bin/env python3
"""
🔑 Connexion
-----------

Page de connexion pour accéder à l'application.
"""

from pathlib import Path
import streamlit as st

from config.config import StreamlitConfig
from utils.auth import authenticate_user, validate_session, logout_user
from utils.sidebar import show_footer


def setup_auth_sidebar():
    """Configure une sidebar simplifiée pour les pages d'authentification."""
    # CSS pour masquer la sidebar automatique de Streamlit
    st.markdown("""
    <style>
    /* Masquer les éléments automatiques de la sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [data-testid="stSidebarSearch"],
    section[data-testid="stSidebar"] [data-testid="stSidebarHistory"],
    section[data-testid="stSidebar"] [data-testid="stSidebarMenu"] {
        display: none !important;
    }
    
    /* Masquer le contenu automatique mais préserver la scrollbar et le bouton de fermeture */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div:not([data-testid="stSidebarUserContent"]):not([data-testid="stSidebarCloseButton"]) {
        display: none !important;
    }
    
    /* S'assurer que le bouton de fermeture reste visible */
    section[data-testid="stSidebar"] [data-testid="stSidebarCloseButton"],
    section[data-testid="stSidebar"] button[aria-label*="Close"],
    section[data-testid="stSidebar"] button[aria-label*="Fermer"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 9999 !important;
    }
    
    /* Préserver la scrollbar de la sidebar */
    section[data-testid="stSidebar"] {
        overflow-y: auto !important;
        scrollbar-width: thin !important;
        scrollbar-color: rgba(181, 101, 118, 0.45) #111111 !important;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 8px !important;
        height: 8px !important;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: #111111 !important;
        border-radius: 4px !important;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: rgba(181, 101, 118, 0.45) !important;
        border-radius: 6px !important;
        border: 2px solid transparent !important;
        background-clip: padding-box !important;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(181, 101, 118, 0.65) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # CSS identique à l'application principale
    st.markdown("""
    <style>
    /* Fond noir pour toute l'application */
    .stApp {
        background-color: #000000 !important;
    }
    
    .main {
        background-color: #000000 !important;
    }
    
    .block-container {
        background-color: #000000 !important;
    }
    
    /* Fond noir pour la sidebar */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 2px solid #b56576 !important; /* bordeaux clair */
        box-shadow: 2px 0 4px rgba(181, 101, 118, 0.25);
    }
    
    /* Scrollbar en bordeaux clair (tous conteneurs) */
    section[data-testid="stSidebar"],
    div[data-testid="stAppViewContainer"] {
        scrollbar-width: thin; /* Firefox */
        scrollbar-color: rgba(181, 101, 118, 0.45) #111111; /* Firefox: thumb track */
    }
    
    /* WebKit (Chrome/Edge/Safari) - appliquer aux zones défilantes principales */
    section[data-testid="stSidebar"] ::-webkit-scrollbar,
    div[data-testid="stAppViewContainer"] ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track,
    div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-track {
        background: #111111;
        border-radius: 4px;
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb,
    div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb {
        background: rgba(181, 101, 118, 0.45);
        border-radius: 6px;
        border: 2px solid transparent; /* évite l'effet de superposition grise */
        background-clip: padding-box;  /* garde les bords nets sans overlay */
    }
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover,
    div[data-testid="stAppViewContainer"] ::-webkit-scrollbar-thumb:hover {
        background: rgba(181, 101, 118, 0.65);
    }
    
    /* Liens de page (st.page_link) stylés comme des boutons */
    /* Encadrer et harmoniser TOUS les liens de page dans la sidebar */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"],
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"],
    section[data-testid="stSidebar"] a[href*="pages/"] {
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        text-decoration: none !important;
        color: #e5e7eb !important; /* gris clair lisible */
        margin: 0.28rem 0 !important; /* espace un peu plus généreux */
        padding: 0.55rem 0.95rem !important; /* soft */
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        background: #141414 !important;
        box-sizing: border-box !important;
        transition: background-color .15s ease, border-color .15s ease, box-shadow .15s ease, color .15s ease !important;
        position: relative !important; /* pour positionner le marqueur actif */
    }
    section[data-testid="stSidebar"] a[data-testid="stPageLink"]:hover,
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"]:hover,
    section[data-testid="stSidebar"] a[href*="pages/"]:hover {
        background: #1a1a1a !important;
        border-color: rgba(255,154,102,0.45) !important;
        box-shadow: 0 0 0 2px rgba(255,154,102,0.25), 0 0 12px rgba(255,154,102,0.28) !important; /* lueur externe douce */
    }
    /* Page active via aria-current OU via marqueurs (classe/is-active ou data-nav-active) */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"],
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"],
    section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"],
    section[data-testid="stSidebar"] a.is-active,
    section[data-testid="stSidebar"] a[data-nav-active="true"] {
        box-shadow: inset 0 0 0 2px #ff9a66 !important; /* contour orange net */
        border-color: #ff9a66 !important;
        background: transparent !important; /* non opaque */
        color: #ff9a66 !important;
        font-weight: 600 !important;
    }
    /* Marqueur: point orange en extrémité droite pour la page active */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]::after,
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"]::after,
    section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"]::after,
    section[data-testid="stSidebar"] a.is-active::after,
    section[data-testid="stSidebar"] a[data-nav-active="true"]::after {
        content: "";
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #ff9a66;
        box-shadow: 0 0 0 2px rgba(255,154,102,0.25);
    }
    /* Lueur externe supplémentaire quand la page active est survolée */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a.is-active:hover,
    section[data-testid="stSidebar"] a[data-nav-active="true"]:hover {
        box-shadow: inset 0 0 0 2px #ff9a66, 0 0 12px rgba(255,154,102,0.32) !important;
    }
    
    /* Réduire l'espace vertical général dans la sidebar */
    section[data-testid="stSidebar"] > div { gap: 0.25rem !important; }
    
    /* Styles pour les boutons de la sidebar */
    .stButton > button {
        background: linear-gradient(90deg, #ff6b35 0%, #f7931e 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # Logo en haut - Responsive
        try:
            logo_path = Path("assets/images/logo_app.png")
            if logo_path.exists():
                st.image(str(logo_path), width=200, use_container_width=False)
            else:
                # Fallback avec emoji si le logo n'existe pas
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="background: white; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <span style="font-size: 60px;">🏗️</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            # Fallback avec emoji en cas d'erreur
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0;">
                <div style="background: white; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                    <span style="font-size: 60px;">🏗️</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Nom de l'app en bas du logo
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h3 style="color: #1e3c72; margin: 0; font-weight: bold; font-size: clamp(14px, 2vw, 18px);">CRACK DETECTION</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Statut de connexion
        st.warning("❌ Non connecté")
        
        st.markdown("---")
        
        # Navigation simple
        st.markdown("### 🏠 Navigation")
        if st.button("🏠 Accueil", key="nav_home_auth"):
            st.switch_page("app.py")
        
        st.markdown("---")
        
        # Lien vers l'inscription
        st.markdown("### 🔐 Pas encore de compte ?")
        if st.button("🔐 S'inscrire", key="nav_register_auth", use_container_width=True):
            st.switch_page("pages/🔐_Inscription.py")


def setup_page():
    """Configure la page."""
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    setup_auth_sidebar()


def check_session():
    """Vérifie si l'utilisateur est déjà connecté."""
    if "session_token" in st.session_state:
        user_info = validate_session(st.session_state.session_token)
        if user_info:
            return user_info
        else:
            # Session expirée, nettoyer
            del st.session_state.session_token
            if "user_info" in st.session_state:
                del st.session_state.user_info
    return None


def main():
    """Fonction principale."""
    setup_page()
    
    # Vérifier si déjà connecté
    user_info = check_session()
    if user_info:
        st.success(f"✅ Bienvenue {user_info['first_name']} !")
        st.info("Vous êtes déjà connecté. Accédez à l'application via le menu.")
        
        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter"):
            if logout_user(st.session_state.session_token):
                del st.session_state.session_token
                if "user_info" in st.session_state:
                    del st.session_state.user_info
                st.success("✅ Déconnexion réussie")
                st.rerun()
        
        return
    
    st.markdown("# 🔑 Connexion")
    st.markdown("Connectez-vous à votre compte pour accéder à l'application.")
    
    # Formulaire de connexion
    with st.form("connexion_form"):
        st.markdown("### 📝 Identifiants")
        
        username = st.text_input(
            "Nom d'utilisateur ou Email *",
            placeholder="Votre nom d'utilisateur ou email"
        )
        
        password = st.text_input(
            "Mot de passe *",
            type="password",
            placeholder="Votre mot de passe"
        )
        
        # Options supplémentaires
        col1, col2 = st.columns(2)
        with col1:
            remember_me = st.checkbox("Se souvenir de moi", value=False)
        with col2:
            show_password = st.checkbox("Afficher le mot de passe", value=False)
        
        if show_password:
            st.text_input("Mot de passe (visible)", value=password, disabled=True)
        
        # Bouton de connexion
        submitted = st.form_submit_button("🔐 Se connecter", type="primary")
        
        if submitted:
            if not username or not password:
                st.error("❌ Veuillez remplir tous les champs")
                return
            
            # Authentification
            with st.spinner("🔄 Authentification en cours..."):
                result = authenticate_user(username, password)
            
            if result["success"]:
                # Stocker la session
                st.session_state.session_token = result["session_token"]
                st.session_state.user_info = result["user"]
                
                st.success(f"✅ Connexion réussie ! Bienvenue {result['user']['first_name']}")
                
                # Afficher les informations de session
                with st.expander("📋 Informations de session"):
                    st.write(f"**Nom d'utilisateur :** {result['user']['username']}")
                    st.write(f"**Nom complet :** {result['user']['first_name']} {result['user']['last_name']}")
                    st.write(f"**Rôle :** {result['user']['role']}")
                    st.write(f"**Session valide jusqu'au :** 7 jours")
                
                # Redirection
                st.markdown("---")
                st.markdown("### 🎯 Accès à l'application")
                st.markdown("Vous pouvez maintenant accéder à toutes les fonctionnalités selon votre rôle :")
                
                role_features = {
                    "client": ["🔍 Analyse Simple", "📜 Historique Personnel"],
                    "inspector": ["🔍 Analyse Simple", "📹 Temps Réel", "📊 Analyse Batch", "📜 Historique", "📤 Export"],
                    "expert": ["🔍 Analyse Simple", "📹 Temps Réel", "📊 Analyse Batch", "📜 Historique Complet", "📤 Export", "✅ Validation"],
                    "admin": ["🔍 Toutes les fonctionnalités", "🛡️ Dashboard Admin", "👥 Gestion Utilisateurs"]
                }
                
                features = role_features.get(result['user']['role'], [])
                for feature in features:
                    st.markdown(f"- {feature}")
                
                # Redirection vers la page principale
                st.switch_page("app.py")
                
            else:
                st.error(f"❌ Échec de la connexion : {result['error']}")
                
                # Aide pour les problèmes courants
                if "verrouillé" in result['error'].lower():
                    st.warning("🔒 Votre compte est temporairement verrouillé. Réessayez dans 30 minutes.")
                elif "incorrect" in result['error'].lower():
                    st.info("💡 Vérifiez votre nom d'utilisateur/email et mot de passe.")
    
    # Informations et liens
    st.markdown("---")
    st.markdown("### 🔗 Liens utiles")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔐 Pas encore de compte ?**")
        if st.button("🔐 Créer un compte", key="go_to_register", use_container_width=True):
            st.switch_page("pages/🔐_Inscription.py")
    
    with col2:
        st.markdown("**❓ Besoin d'aide ?**")
        if st.button("💬 Support", key="go_to_chat", use_container_width=True):
            st.switch_page("pages/💬_Chat_Assistant.py")
    
    # Informations de sécurité
    st.markdown("---")
    st.markdown("### 🔒 Sécurité")
    
    security_info = {
        "🔐 Sessions sécurisées": "Vos sessions expirent automatiquement après 7 jours",
        "🛡️ Protection par force brute": "Votre compte est verrouillé après 5 tentatives échouées",
        "🔒 Mots de passe hachés": "Vos mots de passe sont cryptés avec des algorithmes sécurisés",
        "📊 Logs de connexion": "Toutes les tentatives de connexion sont enregistrées"
    }
    
    for title, description in security_info.items():
        st.markdown(f"**{title}** : {description}")
    
    # Démos et exemples
    st.markdown("---")
    st.markdown("### 🎯 Démonstration")
    
    if st.button("👤 Tester avec un compte démo"):
        st.info("""
        **Compte de démonstration :**
        - **Nom d'utilisateur :** demo
        - **Mot de passe :** Demo123!
        - **Rôle :** Inspecteur
        
        Ce compte vous permet de tester toutes les fonctionnalités de l'application.
        """)
        
        # Créer automatiquement un compte démo si nécessaire
        from utils.auth import register_user
        result = register_user(
            username="demo",
            email="demo@example.com",
            password="Demo123!",
            first_name="Démo",
            last_name="Utilisateur",
            role="inspector"
        )
        
        if result["success"]:
            st.success("✅ Compte démo créé ! Vous pouvez maintenant vous connecter.")
        else:
            st.info("ℹ️ Le compte démo existe déjà ou une erreur s'est produite.")
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()
