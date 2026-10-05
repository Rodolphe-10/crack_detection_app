#!/usr/bin/env python3
"""
🔐 Inscription
-------------

Page d'inscription pour créer un nouveau compte utilisateur.
"""

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

from config.config import StreamlitConfig
from utils.auth import register_user, ROLES, validate_password_strength
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
        
        # Lien vers la connexion
        st.markdown("### 🔑 Déjà un compte ?")
        if st.button("🔑 Se connecter", key="nav_login_auth", use_container_width=True):
            st.switch_page("pages/🔑_Connexion.py")


def setup_page():
    """Configure la page."""
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    setup_auth_sidebar()


def create_avatar_placeholder(letter: str, color: str, size: int = 100) -> bytes:
    """Crée un avatar avec la première lettre du prénom."""
    # Créer une image carrée
    img = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(img)
    
    # Essayer de charger une police, sinon utiliser la police par défaut
    try:
        font_size = size // 2
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Centrer le texte
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    # Dessiner le texte en blanc
    draw.text((x, y), letter, fill='white', font=font)
    
    # Convertir en bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


# Note: La fonction validate_password a été déplacée vers utils.auth.validate_password_strength


def main():
    """Fonction principale."""
    setup_page()
    
    st.markdown("# 🔐 Inscription")
    st.markdown("Créez votre compte pour accéder à l'application de détection de fissures.")
    
    # Formulaire d'inscription
    with st.form("inscription_form", clear_on_submit=True):
        st.markdown("### 📝 Informations Personnelles")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Prénom *", placeholder="Votre prénom")
        with col2:
            last_name = st.text_input("Nom *", placeholder="Votre nom")
        
        email = st.text_input("Email *", placeholder="votre.email@exemple.com")
        username = st.text_input("Nom d'utilisateur *", placeholder="nom_utilisateur")
        
        st.markdown("### 🔒 Sécurité")
        password = st.text_input("Mot de passe *", type="password", placeholder="Mot de passe")
        confirm_password = st.text_input("Confirmer le mot de passe *", type="password", placeholder="Confirmez le mot de passe")
        
        # Validation du mot de passe en temps réel
        if password:
            is_valid, message = validate_password_strength(password)
            if is_valid:
                st.success(message)
            else:
                st.error(message)
        
        # Rôle
        st.markdown("### 🎯 Rôle")
        role = st.selectbox(
            "Choisissez votre rôle *",
            options=list(ROLES.keys()),
            format_func=lambda x: ROLES[x],
            help="Le rôle détermine vos permissions dans l'application"
        )
        
        # Description des rôles
        role_descriptions = {
            "client": "Accès aux analyses simples et historique personnel",
            "inspector": "Analyses complètes, temps réel, batch et export de rapports",
            "expert": "Toutes les fonctionnalités + validation des analyses critiques",
            "admin": "Accès complet + gestion des utilisateurs et système"
        }
        st.info(f"**{ROLES[role]}** : {role_descriptions[role]}")
        
        # Photo de profil
        st.markdown("### 📸 Photo de Profil (Optionnel)")
        profile_photo = st.file_uploader(
            "Ajoutez une photo de profil",
            type=['jpg', 'jpeg', 'png'],
            help="Si aucune photo n'est fournie, un avatar avec votre initiale sera créé"
        )
        
        # Aperçu de l'avatar
        if first_name:
            avatar_letter = first_name[0].upper()
            avatar_color = "#667eea"  # Couleur par défaut
            
            if profile_photo:
                st.image(profile_photo, caption="Votre photo de profil", width=100)
            else:
                avatar_bytes = create_avatar_placeholder(avatar_letter, avatar_color)
                st.image(avatar_bytes, caption=f"Avatar généré : {avatar_letter}", width=100)
        
        # Conditions d'utilisation
        st.markdown("### 📋 Conditions")
        accept_terms = st.checkbox(
            "J'accepte les conditions d'utilisation et la politique de confidentialité *",
            help="Vous devez accepter les conditions pour créer un compte"
        )
        
        # Bouton d'inscription
        submitted = st.form_submit_button("🚀 Créer mon compte", type="primary")
        
        if submitted:
            # Validation des champs requis
            if not all([first_name, last_name, email, username, password, confirm_password, accept_terms]):
                st.error("❌ Tous les champs marqués d'un * sont obligatoires")
                return
            
            # Validation du mot de passe
            if not validate_password_strength(password)[0]:
                st.error("❌ Le mot de passe ne respecte pas les critères de sécurité")
                return
            
            # Validation de la confirmation
            if password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
                return
            
            # Validation de l'email
            if "@" not in email or "." not in email:
                st.error("❌ Format d'email invalide")
                return
            
            # Traitement de la photo de profil
            photo_bytes = None
            if profile_photo:
                try:
                    # Redimensionner et optimiser l'image
                    img = Image.open(profile_photo)
                    img.thumbnail((200, 200))  # Redimensionner à 200x200 max
                    
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG', optimize=True)
                    photo_bytes = buffer.getvalue()
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors du traitement de l'image : {e}")
            
            # Inscription
            with st.spinner("🔄 Création de votre compte..."):
                result = register_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    profile_photo=photo_bytes
                )
            
            if result["success"]:
                # Connexion automatique après inscription
                from utils.auth import authenticate_user
                
                with st.spinner("🔄 Connexion automatique en cours..."):
                    login_result = authenticate_user(username, password)
                
                if login_result["success"]:
                    # Stocker la session
                    st.session_state.session_token = login_result["session_token"]
                    st.session_state.user_info = login_result["user"]
                    
                    st.success("✅ Compte créé et connexion réussie !")
                    st.info(f"🎉 Bienvenue {first_name} ! Vous êtes maintenant connecté.")
                    
                    # Afficher les informations du compte
                    with st.expander("📋 Détails de votre compte"):
                        st.write(f"**Nom d'utilisateur :** {username}")
                        st.write(f"**Email :** {email}")
                        st.write(f"**Nom complet :** {first_name} {last_name}")
                        st.write(f"**Rôle :** {ROLES[role]}")
                        st.write(f"**ID utilisateur :** {result['user_id']}")
                    
                    # Redirection vers l'application principale
                    st.markdown("---")
                    st.markdown("### 🎯 Accès à l'application")
                    st.markdown("Vous pouvez maintenant accéder à toutes les fonctionnalités selon votre rôle :")
                    
                    role_features = {
                        "client": ["🔍 Analyse Simple", "📜 Historique Personnel"],
                        "inspector": ["🔍 Analyse Simple", "📹 Temps Réel", "📊 Analyse Batch", "📜 Historique", "📤 Export"],
                        "expert": ["🔍 Analyse Simple", "📹 Temps Réel", "📊 Analyse Batch", "📜 Historique Complet", "📤 Export", "✅ Validation"],
                        "admin": ["🔍 Toutes les fonctionnalités", "🛡️ Dashboard Admin", "👥 Gestion Utilisateurs"]
                    }
                    
                    features = role_features.get(role, [])
                    for feature in features:
                        st.markdown(f"- {feature}")
                    
                    # Redirection automatique vers l'application
                    st.markdown("---")
                    st.markdown("⏳ Redirection automatique vers l'application...")
                    st.switch_page("app.py")
                    
                else:
                    st.success("✅ Compte créé avec succès !")
                    st.warning("⚠️ Connexion automatique échouée. Veuillez vous connecter manuellement.")
                    
                    # Afficher les informations du compte
                    with st.expander("📋 Détails de votre compte"):
                        st.write(f"**Nom d'utilisateur :** {username}")
                        st.write(f"**Email :** {email}")
                        st.write(f"**Nom complet :** {first_name} {last_name}")
                        st.write(f"**Rôle :** {ROLES[role]}")
                        st.write(f"**ID utilisateur :** {result['user_id']}")
                    
                    # Redirection vers la connexion
                    st.markdown("---")
                    st.markdown("### 🔗 Prochaines étapes")
                    st.markdown("1. **Connectez-vous** avec vos identifiants")
                    st.markdown("2. **Explorez l'application** selon votre rôle")
                    st.markdown("3. **Commencez vos analyses** de détection de fissures")
                
            else:
                st.error(f"❌ Erreur lors de la création : {result['error']}")
    
    # Informations supplémentaires
    st.markdown("---")
    st.markdown("### 💡 Informations")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🔒 Sécurité**")
        st.markdown("- Mots de passe hachés avec salt")
        st.markdown("- Sessions sécurisées")
        st.markdown("- Protection contre les attaques par force brute")
    
    with col2:
        st.markdown("**📊 Données**")
        st.markdown("- Vos données sont privées")
        st.markdown("- Historique personnel")
        st.markdown("- Profil personnalisable")
    
    # Lien vers la connexion
    st.markdown("---")
    st.markdown("### 🔐 Déjà un compte ?")
    st.markdown("Connectez-vous pour accéder à votre espace.")
    if st.button("🔑 Se connecter", key="go_to_login", use_container_width=True):
        st.switch_page("pages/🔑_Connexion.py")
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()
