#!/usr/bin/env python3
"""
👤 Profil Utilisateur
--------------------

Page de gestion du profil utilisateur.
"""

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

from config.config import StreamlitConfig
from utils.auth import (
    validate_session, get_user_info, update_user_profile, 
    change_password, logout_user, ROLES, validate_password_strength
)
from utils.sidebar import show_unified_sidebar, show_footer


def setup_page():
    """Configure la page."""
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    show_unified_sidebar("Profil")



    # CSS pour masquer la sidebar automatique de Streamlit
    st.markdown("""
    <style>
    /* Masquer uniquement les éléments de navigation automatique */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [data-testid="stSidebarSearch"],
    section[data-testid="stSidebar"] [data-testid="stSidebarHistory"],
    section[data-testid="stSidebar"] [data-testid="stSidebarMenu"] {
        display: none !important;
    }
    
    /* S'assurer que le bouton de fermeture reste visible et accessible */
    section[data-testid="stSidebar"] [data-testid="stSidebarCloseButton"],
    section[data-testid="stSidebar"] button[aria-label*="Close"],
    section[data-testid="stSidebar"] button[aria-label*="Fermer"],
    section[data-testid="stSidebar"] button[aria-label*="close"],
    section[data-testid="stSidebar"] button[aria-label*="fermer"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 9999 !important;
        position: relative !important;
        background: #1e3c72 !important;
        color: white !important;
        border: 2px solid #667eea !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-width: 32px !important;
        min-height: 32px !important;
        padding: 0 !important;
        margin: 0 !important;
        font-size: 16px !important;
        line-height: 1 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stSidebarCloseButton"]:hover,
    section[data-testid="stSidebar"] button[aria-label*="Close"]:hover,
    section[data-testid="stSidebar"] button[aria-label*="Fermer"]:hover {
        background: #667eea !important;
        transform: scale(1.1) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
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
    
    /* S'assurer que la sidebar reste visible */
    section[data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)





def create_avatar_placeholder(letter: str, color: str, size: int = 100) -> bytes:
    """Crée un avatar avec la première lettre du prénom."""
    img = Image.new('RGB', (size, size), color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_size = size // 2
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    
    draw.text((x, y), letter, fill='white', font=font)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


def check_authentication():
    """Vérifie l'authentification de l'utilisateur."""
    if "session_token" not in st.session_state:
        st.error("❌ Vous devez être connecté pour accéder à cette page.")
        st.info("🔐 [Connectez-vous ici](/Connexion)")
        return None
    
    user_info = validate_session(st.session_state.session_token)
    if not user_info:
        st.error("❌ Session expirée. Veuillez vous reconnecter.")
        if "session_token" in st.session_state:
            del st.session_state.session_token
        if "user_info" in st.session_state:
            del st.session_state.user_info
        st.info("🔐 [Reconnectez-vous ici](/Connexion)")
        return None
    
    return user_info


def main():
    """Fonction principale."""
    setup_page()
    
    # Vérifier l'authentification
    user_info = check_authentication()
    if not user_info:
        return
    
    st.markdown("# 👤 Mon Profil")
    st.markdown(f"Gérez vos informations personnelles et paramètres de compte.")
    
    # Récupérer les informations complètes de l'utilisateur
    full_user_info = get_user_info(user_info["user_id"])
    if not full_user_info:
        st.error("❌ Impossible de récupérer les informations du profil.")
        return
    
    # Affichage du profil
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📸 Photo de Profil")
        
        # Afficher la photo de profil ou l'avatar
        if full_user_info["profile_photo"]:
            st.image(full_user_info["profile_photo"], caption="Votre photo de profil", width=150)
        else:
            avatar_bytes = create_avatar_placeholder(
                full_user_info["avatar_letter"], 
                full_user_info["avatar_color"]
            )
            st.image(avatar_bytes, caption=f"Avatar : {full_user_info['avatar_letter']}", width=150)
    
    with col2:
        st.markdown("### 📋 Informations Personnelles")
        
        # Informations en lecture seule
        st.write(f"**Nom d'utilisateur :** {full_user_info['username']}")
        st.write(f"**Email :** {full_user_info['email']}")
        st.write(f"**Prénom :** {full_user_info['first_name']}")
        st.write(f"**Nom :** {full_user_info['last_name']}")
        st.write(f"**Rôle :** {ROLES.get(full_user_info['role'], full_user_info['role'])}")
        st.write(f"**Membre depuis :** {full_user_info['created_at']}")
        if full_user_info['last_login']:
            st.write(f"**Dernière connexion :** {full_user_info['last_login']}")
    
    # Onglets pour différentes sections
    tab1, tab2, tab3, tab4 = st.tabs(["✏️ Modifier Profil", "🔒 Changer Mot de Passe", "📊 Statistiques", "⚙️ Paramètres"])
    
    with tab1:
        st.markdown("### ✏️ Modifier les Informations")
        
        with st.form("update_profile_form"):
            new_first_name = st.text_input("Prénom", value=full_user_info['first_name'])
            new_last_name = st.text_input("Nom", value=full_user_info['last_name'])
            new_email = st.text_input("Email", value=full_user_info['email'])
            
            # Nouvelle photo de profil
            new_profile_photo = st.file_uploader(
                "Nouvelle photo de profil",
                type=['jpg', 'jpeg', 'png'],
                help="Laissez vide pour conserver la photo actuelle"
            )
            
            if new_profile_photo:
                st.image(new_profile_photo, caption="Nouvelle photo", width=100)
            
            submitted = st.form_submit_button("💾 Sauvegarder les modifications")
            
            if submitted:
                # Traitement de la nouvelle photo
                photo_bytes = None
                if new_profile_photo:
                    try:
                        img = Image.open(new_profile_photo)
                        img.thumbnail((200, 200))
                        buffer = io.BytesIO()
                        img.save(buffer, format='PNG', optimize=True)
                        photo_bytes = buffer.getvalue()
                    except Exception as e:
                        st.error(f"❌ Erreur lors du traitement de l'image : {e}")
                        return
                
                # Mise à jour du profil
                result = update_user_profile(
                    user_id=user_info["user_id"],
                    first_name=new_first_name,
                    last_name=new_last_name,
                    email=new_email,
                    profile_photo=photo_bytes
                )
                
                if result["success"]:
                    st.success("✅ Profil mis à jour avec succès !")
                    st.rerun()
                else:
                    st.error(f"❌ Erreur : {result['error']}")
    
    with tab2:
        st.markdown("### 🔒 Changer le Mot de Passe")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Mot de passe actuel", type="password")
            new_password = st.text_input("Nouveau mot de passe", type="password")
            confirm_new_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
            
            # Validation du nouveau mot de passe
            if new_password:
                is_valid, message = validate_password_strength(new_password)
                if is_valid:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            
            submitted = st.form_submit_button("🔐 Changer le mot de passe")
            
            if submitted:
                if not all([current_password, new_password, confirm_new_password]):
                    st.error("❌ Tous les champs sont requis")
                elif new_password != confirm_new_password:
                    st.error("❌ Les nouveaux mots de passe ne correspondent pas")
                else:
                    result = change_password(
                        user_id=user_info["user_id"],
                        current_password=current_password,
                        new_password=new_password
                    )
                    
                    if result["success"]:
                        st.success("✅ Mot de passe changé avec succès !")
                        st.info("🔐 Vous devrez vous reconnecter avec votre nouveau mot de passe.")
                        
                        # Déconnexion automatique
                        if st.button("🚪 Se déconnecter maintenant"):
                            logout_user(st.session_state.session_token)
                            del st.session_state.session_token
                            if "user_info" in st.session_state:
                                del st.session_state.user_info
                            st.success("✅ Déconnexion réussie")
                            st.rerun()
                    else:
                        st.error(f"❌ Erreur : {result['error']}")
    
    with tab3:
        st.markdown("### 📊 Mes Statistiques")
        
        # Statistiques de l'utilisateur (à implémenter avec l'historique)
        from utils.history_store import fetch_history
        
        user_analyses = fetch_history(
            limit=1000,
            page=None,  # Toutes les pages
            method=None,  # Toutes les méthodes
            has_crack=None  # Tous les résultats
        )
        
        if user_analyses:
            # Filtrer les analyses de cet utilisateur (à implémenter)
            # Pour l'instant, afficher toutes les analyses
            total_analyses = len(user_analyses)
            analyses_avec_fissures = sum(1 for a in user_analyses if a["has_crack"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Analyses", total_analyses)
            with col2:
                st.metric("Fissures Détectées", analyses_avec_fissures)
            with col3:
                if total_analyses > 0:
                    taux = (analyses_avec_fissures / total_analyses) * 100
                    st.metric("Taux de Détection", f"{taux:.1f}%")
                else:
                    st.metric("Taux de Détection", "0%")
            
            # Graphique des analyses par page
            if user_analyses:
                import pandas as pd
                df = pd.DataFrame(user_analyses)
                df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
                
                st.markdown("#### 📈 Analyses par Jour")
                daily_counts = df.groupby('date').size()
                st.line_chart(daily_counts)
        else:
            st.info("📊 Aucune analyse effectuée pour le moment.")
            st.markdown("Commencez par effectuer quelques analyses pour voir vos statistiques !")
    
    with tab4:
        st.markdown("### ⚙️ Paramètres du Compte")
        
        # Paramètres de sécurité
        st.markdown("#### 🔒 Sécurité")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Session actuelle**")
            st.write(f"**Token :** {st.session_state.session_token[:20]}...")
            st.write(f"**Expire dans :** 7 jours")
        
        with col2:
            st.info("**Actions de sécurité**")
            if st.button("🔄 Renouveler la session"):
                st.info("ℹ️ Fonctionnalité à implémenter")
        
        # Paramètres de notifications (à implémenter)
        st.markdown("#### 🔔 Notifications")
        st.checkbox("Recevoir des notifications par email", value=False)
        st.checkbox("Notifications de nouvelles analyses", value=False)
        
        # Actions de compte
        st.markdown("#### 🚪 Actions de Compte")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚪 Se déconnecter", type="secondary"):
                if logout_user(st.session_state.session_token):
                    del st.session_state.session_token
                    if "user_info" in st.session_state:
                        del st.session_state.user_info
                    st.success("✅ Déconnexion réussie")
                    st.experimental_rerun()
        
        with col2:
            if st.button("🗑️ Supprimer le compte", type="secondary"):
                st.warning("⚠️ Cette action est irréversible !")
                if st.button("✅ Confirmer la suppression", type="primary"):
                    st.error("❌ Fonctionnalité de suppression à implémenter")
    
    # Informations supplémentaires
    st.markdown("---")
    st.markdown("### 💡 Aide et Support")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**❓ Questions ?**")
        st.markdown("[Chat Assistant](/Chat_Assistant)")
        st.markdown("[Documentation](/Documentation)")
    
    with col2:
        st.markdown("**🔗 Liens utiles**")
        st.markdown("[Historique](/historique)")
        st.markdown("[Tableau de bord](/Tableau_de_Bord)")
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()
