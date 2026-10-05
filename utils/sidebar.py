#!/usr/bin/env python3
"""
Sidebar unifiée pour toutes les pages
"""

import streamlit as st
from pathlib import Path
from utils.auth import get_user_info


def show_footer():
    """Affiche un footer en bas des pages, dans le flux (non fixe).

    - Fond noir, texte blanc, nom du développeur en orange
    - Reste tout en bas: le contenu principal prend au moins la hauteur de l'écran
    """
    st.markdown("""
    <style>
    /* S'assurer que la zone principale occupe la hauteur de la fenêtre 
       moins la hauteur approximative du footer pour pousser le footer en bas
    */
    html, body { height: 100%; }
    .main .block-container {
        min-height: calc(100vh - 80px) !important; /* ~80px = hauteur footer */
    }

    /* Footer dans le flux, en bas de page */
    .footer {
        position: relative !important;
        background: #000000 !important;
        color: #ffffff !important;
        text-align: center !important;
        padding: 1rem !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border-top: 1px solid rgba(255,255,255,0.1) !important;
        margin-top: 3rem !important; /* Espace entre le contenu et le footer */
    }

    .footer .developer-name {
        color: #b56576 !important; /* bordeaux */
        font-weight: 700 !important;
    }
    </style>

    <div class="footer">
        <div>© 2025 Tous droits réservés — Développé par <span class="developer-name">Andrew Mbassi Elessa</span></div>
    </div>
    """, unsafe_allow_html=True)


def show_unified_sidebar(current_page_name=None):
    """Affiche la sidebar unifiée pour toutes les pages."""
    # Initialiser l'historique de navigation
    if "navigation_history" not in st.session_state:
        st.session_state.navigation_history = ["app.py"]
    
    # Ajouter la page actuelle à l'historique si elle n'est pas déjà la dernière
    current_page_path = current_page_name
    if current_page_name:
        # Convertir le nom de la page en chemin
        if current_page_name == "Accueil":
            current_page_path = "app.py"
        else:
            # Chercher le fichier correspondant dans les pages
            page_files = {
                "Détection Simple": "pages/🔍_Detection_Simple.py",
                "Analyse Batch": "pages/📊_Analyse_Batch.py",
                "Détection Temps Réel": "pages/📹_Detection_Temps_Reel.py",
                "Chat Assistant": "pages/💬_Chat_Assistant.py",
                "Tableau de Bord": "pages/📈_Tableau_de_Bord.py",
                "Historique": "pages/historique.py",
                "Profil": "pages/👤_Profil.py",
                "Gestion Utilisateurs": "pages/👥_Gestion_Utilisateurs.py",
                "Dashboard Admin": "pages/🛡️_Dashboard_Admin.py",
                "Connexion": "pages/🔑_Connexion.py",
                "Inscription": "pages/🔐_Inscription.py"
            }
            current_page_path = page_files.get(current_page_name, "app.py")
    
    # Ajouter à l'historique seulement si ce n'est pas la même page
    if not st.session_state.navigation_history or st.session_state.navigation_history[-1] != current_page_path:
        st.session_state.navigation_history.append(current_page_path)
    
    # Limiter l'historique à 10 pages
    if len(st.session_state.navigation_history) > 10:
        st.session_state.navigation_history = st.session_state.navigation_history[-10:]
    
    # CSS pour le fond noir de la sidebar
    st.markdown("""
    <style>
    /* Fond noir pour la sidebar */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
        border-right: 2px solid #b56576 !important; /* bordeaux clair */
        box-shadow: 2px 0 4px rgba(181, 101, 118, 0.25);
    }
    
    /* Style pour les boutons Retour et Accueil */
    .sidebar .stButton > button[key="nav_back"],
    .sidebar .stButton > button[key="nav_home"] {
        height: 35px !important;
        font-size: 12px !important;
        padding: 0.5rem 0.75rem !important;
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
                    <div style="background: black; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <span style="font-size: 60px;">🏗️</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            # Fallback avec emoji en cas d'erreur
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0;">
                <div style="background: black; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
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
        if st.session_state.user_id:
            st.success(f"✅ Connecté : {st.session_state.username}")
            if st.session_state.is_admin:
                st.info("👑 Administrateur")
        else:
            st.warning("❌ Non connecté")
        
        # Navigation pour les utilisateurs connectés
        if st.session_state.user_id:
            # Avatar et profil utilisateur (en haut)
            user_info = get_user_info(st.session_state.user_id)
            
            if user_info:
                # Créer l'avatar
                if user_info.get('profile_photo'):
                    # Avatar avec photo
                    st.markdown(f"""
                    <div style="text-align: center; margin: 1rem 0; position: relative;">
                        <div style="width: 60px; height: 60px; border-radius: 50%; margin: 0 auto; overflow: hidden; border: 3px solid #1e3c72; position: relative;">
                            <img src="data:image/jpeg;base64,{user_info['profile_photo']}" 
                                 style="width: 100%; height: 100%; object-fit: cover;" />
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #e5e7eb; text-align: center;">{user_info['first_name']} {user_info['last_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Avatar avec initiale
                    avatar_letter = user_info.get('avatar_letter', user_info['first_name'][0].upper())
                    avatar_color = user_info.get('avatar_color', '#667eea')
                    st.markdown(f"""
                    <div style="text-align: center; margin: 1rem 0; position: relative;">
                        <div style="width: 60px; height: 60px; border-radius: 50%; background: {avatar_color}; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; font-size: 24px; font-weight: bold; color: white; position: relative;">
                            {avatar_letter}
                        </div>
                        <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #e5e7eb; text-align: center;">{user_info['first_name']} {user_info['last_name']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Bouton centré pour le profil
            if st.button("👤 Mon Profil", key="nav_profile", help="Gérer votre profil", use_container_width=True):
                st.switch_page("pages/👤_Profil.py")
            
            # Boutons Retour et Accueil directement après le profil
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Retour", key="nav_back", help="Page précédente", use_container_width=True):
                    # Logique de retour améliorée
                    if "navigation_history" in st.session_state and len(st.session_state.navigation_history) > 1:
                        # Retourner à la page précédente
                        previous_page = st.session_state.navigation_history[-2]
                        st.switch_page(previous_page)
                    else:
                        # Par défaut, retour à l'accueil
                        st.switch_page("app.py")
            
            with col2:
                if st.button("🏠 Accueil", key="nav_home", help="Retour à l'accueil", use_container_width=True):
                    st.switch_page("app.py")
            
            # Fonctionnalités administrateur uniquement (après les boutons de navigation)
            if st.session_state.is_admin:
                st.markdown("---")
                st.markdown("### 🛡️ Administration")
                
                if st.button("👥 Gestion Utilisateurs", key="nav_users", help="Gérer les utilisateurs", use_container_width=True):
                    st.switch_page("pages/👥_Gestion_Utilisateurs.py")
                
                if st.button("🛡️ Dashboard Admin", key="nav_admin_dashboard", help="Dashboard administrateur", use_container_width=True):
                    st.switch_page("pages/🛡️_Dashboard_Admin.py")
            
            st.markdown("---")
            
            # Navigation principale
            st.markdown("### 🚀 Navigation")
            
            # Fonctionnalités principales avec style uniforme
            if st.button("🔍 Détection Simple", key="nav_simple", help="Analyse d'image simple", use_container_width=True):
                st.switch_page("pages/🔍_Detection_Simple.py")
            
            if st.button("📊 Analyse Batch", key="nav_batch", help="Analyse de plusieurs images", use_container_width=True):
                st.switch_page("pages/📊_Analyse_Batch.py")
            
            if st.button("📹 Détection Temps Réel", key="nav_realtime", help="Analyse en temps réel", use_container_width=True):
                st.switch_page("pages/📹_Detection_Temps_Reel.py")
            
            if st.button("💬 Chat Assistant", key="nav_chat", help="Assistant IA", use_container_width=True):
                st.switch_page("pages/💬_Chat_Assistant.py")
            
            if st.button("📈 Tableau de Bord", key="nav_dashboard", help="Voir vos statistiques", use_container_width=True):
                st.switch_page("pages/📈_Tableau_de_Bord.py")
            
            if st.button("📋 Historique", key="nav_history", help="Historique des analyses", use_container_width=True):
                st.switch_page("pages/historique.py")
            
            st.markdown("---")
            
            if st.button("🚪 Déconnexion", key="logout", help="Se déconnecter", use_container_width=True):
                # Nettoyer la session
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.session_state.session_token = None
                st.session_state.user_info = None
                st.rerun()
        else:
            # Titre d'authentification avec espacement réduit
            st.markdown("## 🔐 Authentification")
            
            # Formulaire de connexion amélioré
            with st.form("sidebar_login_form", clear_on_submit=False):
                st.markdown("""
                <style>
                /* Style pour les titres centrés */
                .sidebar .sidebar-content h3 {
                    text-align: center !important;
                    margin-bottom: 1rem !important;
                }
                
                /* Style uniforme pour tous les boutons de la sidebar */
                .sidebar .stButton > button {
                    width: 100% !important;
                    height: 45px !important;
                    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 8px !important;
                    padding: 0.75rem 1rem !important;
                    font-weight: 500 !important;
                    font-size: 14px !important;
                    transition: all 0.3s ease !important;
                    margin-bottom: 0.5rem !important;
                    text-align: center !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                
                .sidebar .stButton > button:hover {
                    background: linear-gradient(90deg, #2a5298 0%, #3a6bb8 100%) !important;
                    transform: translateY(-1px) !important;
                    box-shadow: 0 4px 8px rgba(30, 60, 114, 0.3) !important;
                }
                
                /* Style spécial pour le bouton de déconnexion */
                .sidebar .stButton > button[key="logout"] {
                    background: linear-gradient(90deg, #dc3545 0%, #c82333 100%) !important;
                }
                
                .sidebar .stButton > button[key="logout"]:hover {
                    background: linear-gradient(90deg, #c82333 0%, #bd2130 100%) !important;
                }
                
                /* Style pour les champs de texte */
                .stTextInput > div > div > input {
                    background-color: rgba(255,255,255,0.1) !important;
                    border: 1px solid rgba(255,255,255,0.2) !important;
                    border-radius: 8px !important;
                    color: white !important;
                    padding: 0.75rem !important;
                }
                .stTextInput > div > div > input:focus {
                    border-color: #ff6b35 !important;
                    box-shadow: 0 0 0 2px rgba(255,107,53,0.25) !important;
                }
                .stTextInput > label {
                    color: #e5e7eb !important;
                    font-weight: 500 !important;
                    margin-bottom: 0.5rem !important;
                }
                
                /* Style pour le bouton de connexion */
                .stButton > button {
                    background: linear-gradient(90deg, #ff6b35 0%, #f7931e 100%) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 25px !important;
                    padding: 0.75rem 2rem !important;
                    font-weight: bold !important;
                    font-size: 16px !important;
                    transition: all 0.3s ease !important;
                    width: 100% !important;
                }
                .stButton > button:hover {
                    transform: translateY(-2px) !important;
                    box-shadow: 0 4px 12px rgba(255,107,53,0.4) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.text_input("👤 Nom d'utilisateur ou Email", key="sidebar_username", placeholder="Entrez votre identifiant")
                st.text_input("🔒 Mot de passe", type="password", key="sidebar_password", placeholder="Entrez votre mot de passe")
                
                if st.form_submit_button("🔑 Se connecter", use_container_width=True):
                    username = st.session_state.get("sidebar_username", "")
                    password = st.session_state.get("sidebar_password", "")
                    if username and password:
                        # Utiliser le nouveau système d'authentification
                        from utils.auth import authenticate_user
                        result = authenticate_user(username, password)
                        if result["success"]:
                            # Stocker la session avec le nouveau système
                            st.session_state.session_token = result["session_token"]
                            st.session_state.user_info = result["user"]
                            # Synchroniser avec l'ancien système pour compatibilité
                            st.session_state.user_id = result["user"]["id"]
                            st.session_state.username = result["user"]["username"]
                            st.session_state.is_admin = result["user"]["role"] == "admin"
                            st.success("✅ Connexion réussie !")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['error']}")
                    else:
                        st.warning("⚠️ Veuillez remplir tous les champs.")
            
            st.markdown("---")
            
            # Lien vers l'inscription amélioré
            st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <p style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.5rem;">Pas encore de compte ?</p>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🔐 Créer un compte", key="nav_register", help="Créer un compte", use_container_width=True):
                st.switch_page("pages/��_Inscription.py")
