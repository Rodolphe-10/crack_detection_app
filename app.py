#!/usr/bin/env python3
"""
Application Streamlit - Détecteur de Fissures IA
===============================================

Application professionnelle pour la détection et segmentation
de fissures dans les structures en béton.
"""

import streamlit as st
import sqlite3
import hashlib
import os
import sys
from datetime import datetime
import pandas as pd
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="🔍 Système de Détection de Fissures",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Ajout du CSS personnalisé
st.markdown("""
<style>
    /* Masquer les éléments automatiques de la sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [data-testid="stSidebarSearch"],
    section[data-testid="stSidebar"] [data-testid="stSidebarHistory"],
    section[data-testid="stSidebar"] [data-testid="stSidebarMenu"] {
        display: none !important;
    }
    
    /* Ne pas masquer le conteneur générique du contenu de la sidebar
       (sinon le bouton de fermeture peut disparaître sur certaines pages) */
    
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
        border-color: rgba(230,126,34,0.45) !important;
        box-shadow: 0 0 0 2px rgba(230,126,34,0.25), 0 0 12px rgba(230,126,34,0.28) !important; /* lueur externe douce */
    }
    /* Page active via aria-current OU via marqueurs (classe/is-active ou data-nav-active) */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"],
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"],
    section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"],
    section[data-testid="stSidebar"] a.is-active,
    section[data-testid="stSidebar"] a[data-nav-active="true"] {
        box-shadow: inset 0 0 0 2px #e67e22 !important; /* contour orange net */
        border-color: #e67e22 !important;
        background: transparent !important; /* non opaque */
        color: #e67e22 !important;
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
        background: #e67e22;
        box-shadow: 0 0 0 2px rgba(230,126,34,0.25);
    }
    /* Lueur externe supplémentaire quand la page active est survolée */
    section[data-testid="stSidebar"] a[data-testid="stPageLink"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a[data-testid^="stPageLink"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a[href*="pages/"][aria-current="page"]:hover,
    section[data-testid="stSidebar"] a.is-active:hover,
    section[data-testid="stSidebar"] a[data-nav-active="true"]:hover {
        box-shadow: inset 0 0 0 2px #e67e22, 0 0 12px rgba(230,126,34,0.32) !important;
    }
    
    /* Réduire l'espace vertical général dans la sidebar */
    section[data-testid="stSidebar"] > div { gap: 0.25rem !important; }
    
    .main-header {
        background: linear-gradient(90deg, #e67e22 0%, #d35400 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .auth-container {
        background: #000000;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .feature-card {
        background: #1a1a1a;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin: 1rem 0;
        border-left: 4px solid #e67e22;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #e67e22 0%, #d35400 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(230, 126, 34, 0.3);
    }
    
    .auth-button {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%) !important;
    }
    
    .logout-button {
        background: linear-gradient(90deg, #f44336 0%, #da190b 100%) !important;
    }
    
    .active-page-button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%) !important;
        border: 2px solid #e67e22 !important;
        box-shadow: 0 0 10px rgba(230, 126, 34, 0.5) !important;
        transform: scale(1.05) !important;
    }
    
    .active-page-button:hover {
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%) !important;
        transform: scale(1.05) translateY(-2px) !important;
    }
    
    .nav-button {
        transition: all 0.3s ease;
        border-radius: 10px;
        margin: 0.2rem 0;
    }
    
    .nav-button:hover {
        transform: translateX(5px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
</style>
    """, unsafe_allow_html=True)

# Initialisation de la session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Accueil"
if 'session_token' not in st.session_state:
    st.session_state.session_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# Synchronisation avec le nouveau système d'authentification
if st.session_state.session_token and st.session_state.user_info:
    st.session_state.user_id = st.session_state.user_info.get('id')
    st.session_state.username = st.session_state.user_info.get('username')
    st.session_state.is_admin = st.session_state.user_info.get('role') == 'admin'

def _current_page_key():
    """Détermine la clé de la page actuelle basée sur l'URL."""
    try:
        # Utiliser st.query_params pour détecter la page actuelle
        query_params = st.query_params
        if 'page' in query_params:
            return query_params['page']
        
        # Fallback: utiliser le nom du fichier
        import os
        current_file = os.path.basename(__file__)
        
        # Mapping des pages
        page_mapping = {
            "app.py": "Accueil",
            "🔍_Detection_Simple.py": "Detection_Simple",
            "📊_Analyse_Batch.py": "Analyse_Batch",
            "📹_Detection_Temps_Reel.py": "Detection_Temps_Reel",
            "📈_Tableau_de_Bord.py": "Tableau_de_Bord",
            "💬_Chat_Assistant.py": "Chat_Assistant",
            "historique.py": "Historique",
            "👤_Profil.py": "Profil",
            "🔑_Connexion.py": "Connexion",
            "🔐_Inscription.py": "Inscription"
        }
        
        return page_mapping.get(current_file, "Accueil")
    except:
        return "Accueil"

def init_database():
    """Initialise la base de données avec les tables nécessaires."""
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_admin BOOLEAN DEFAULT 0,
            last_login TIMESTAMP
        )
    ''')
    
    # Table de l'historique des analyses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            image_path TEXT,
            result TEXT,
            confidence REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash un mot de passe avec SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Vérifie un mot de passe contre son hash."""
    return hash_password(password) == password_hash

def register_user(username, email, password):
    """Enregistre un nouvel utilisateur."""
    try:
        conn = sqlite3.connect('data/users.db')
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        conn.commit()
        conn.close()
        return True, "Inscription réussie !"
    except sqlite3.IntegrityError:
        return False, "Nom d'utilisateur ou email déjà utilisé."
    except Exception as e:
        return False, f"Erreur lors de l'inscription : {str(e)}"

def login_user(username, password):
    """Connecte un utilisateur."""
    try:
        conn = sqlite3.connect('data/users.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, password_hash, is_admin
            FROM users
            WHERE username = ? OR email = ?
        ''', (username, username))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and verify_password(password, user[2]):
            # Mise à jour de la dernière connexion
            conn = sqlite3.connect('data/users.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (user[0],))
            conn.commit()
            conn.close()
            
            return True, user
        else:
            return False, None
    except Exception as e:
        return False, None

def get_user_stats(user_id):
    """Récupère les statistiques d'un utilisateur."""
    try:
        conn = sqlite3.connect('data/users.db')
        cursor = conn.cursor()
        
        # Nombre total d'analyses
        cursor.execute('''
            SELECT COUNT(*) FROM analysis_history WHERE user_id = ?
        ''', (user_id,))
        total_analyses = cursor.fetchone()[0]
        
        # Analyses récentes (7 derniers jours)
        cursor.execute('''
            SELECT COUNT(*) FROM analysis_history 
            WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
        ''', (user_id,))
        recent_analyses = cursor.fetchone()[0]
        
        # Taux de réussite (analyses avec confiance > 0.8)
        cursor.execute('''
            SELECT COUNT(*) FROM analysis_history 
            WHERE user_id = ? AND confidence > 0.8
        ''', (user_id,))
        successful_analyses = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_analyses': total_analyses,
            'recent_analyses': recent_analyses,
            'success_rate': (successful_analyses / total_analyses * 100) if total_analyses > 0 else 0
        }
    except Exception as e:
        return {'total_analyses': 0, 'recent_analyses': 0, 'success_rate': 0}

def show_header():
    """Affiche l'en-tête de l'application."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b35 0%, #f7931e 100%); padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2);">
        <h1 style="color: white; margin-bottom: 1rem; font-size: 2.5rem; font-weight: bold;">🏗️ Détection de Fissures</h1>
        <p style="color: white; font-size: 1.2rem; margin: 0;">Solution Professionnelle pour l'Inspection du Béton</p>
    </div>
    """, unsafe_allow_html=True)

def show_sidebar():
    """Configure la sidebar avec navigation et informations."""
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
        
        # Navigation
        current_page = _current_page_key()
        
        # Navigation pour les utilisateurs connectés
        if st.session_state.user_id:
            # Avatar et profil utilisateur (en haut)
            # Récupérer les infos utilisateur pour l'avatar
            from utils.auth import get_user_info
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
            
            # Bouton centré pour le profil avec indication de page active
            current_page = _current_page_key()
            is_active = current_page == "Profil"
            if st.button("👤 Mon Profil", key="nav_profile", help="Gérer votre profil", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/👤_Profil.py")
            
            # Fonctionnalités administrateur uniquement (après le profil)
            if st.session_state.is_admin:
                st.markdown("---")
                st.markdown("### 🛡️ Administration")
                
                # Gestion Utilisateurs
                is_active = current_page == "Gestion_Utilisateurs"
                if st.button("👥 Gestion Utilisateurs", key="nav_users", help="Gérer les utilisateurs", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.switch_page("pages/👥_Gestion_Utilisateurs.py")
                
                # Dashboard Admin
                is_active = current_page == "Dashboard_Admin"
                if st.button("🛡️ Dashboard Admin", key="nav_admin_dashboard", help="Dashboard administrateur", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.switch_page("pages/🛡️_Dashboard_Admin.py")
        
        st.markdown("---")
        
        # Navigation principale (uniquement pour les utilisateurs connectés)
        if st.session_state.user_id:
            st.markdown("### 🚀 Navigation")
            
            # Fonctionnalités principales avec style uniforme et indication de page active
            current_page = _current_page_key()
            
            # Détection Simple
            is_active = current_page == "Detection_Simple"
            button_style = "active-page-button" if is_active else ""
            if st.button("🔍 Détection Simple", key="nav_simple", help="Analyse d'image simple", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/🔍_Detection_Simple.py")
            
            # Analyse Batch
            is_active = current_page == "Analyse_Batch"
            if st.button("📊 Analyse Batch", key="nav_batch", help="Analyse de plusieurs images", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/📊_Analyse_Batch.py")
            
            # Détection Temps Réel
            is_active = current_page == "Detection_Temps_Reel"
            if st.button("📹 Détection Temps Réel", key="nav_realtime", help="Analyse en temps réel", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/📹_Detection_Temps_Reel.py")
            
            # Chat Assistant
            is_active = current_page == "Chat_Assistant"
            if st.button("💬 Chat Assistant", key="nav_chat", help="Assistant IA", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/💬_Chat_Assistant.py")
            
            # Tableau de Bord
            is_active = current_page == "Tableau_de_Bord"
            if st.button("📈 Tableau de Bord", key="nav_dashboard", help="Voir vos statistiques", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/📈_Tableau_de_Bord.py")
            
            # Historique
            is_active = current_page == "Historique"
            if st.button("📋 Historique", key="nav_history", help="Historique des analyses", use_container_width=True, type="primary" if is_active else "secondary"):
                st.switch_page("pages/historique.py")
        
        st.markdown("---")
        
        # Bouton de déconnexion pour les utilisateurs connectés
        if st.session_state.user_id:
            if st.button("🚪 Déconnexion", key="logout", help="Se déconnecter", use_container_width=True):
                # Afficher une confirmation de déconnexion sur la zone principale
                st.session_state.show_logout_confirm = True
        
        # Boîte de confirmation de déconnexion (zone principale)
        if st.session_state.get("show_logout_confirm"):
            st.markdown("---")
            st.warning("Êtes-vous sûr de vouloir vous déconnecter ?")
            c1, c2 = st.columns([1,1])
            with c1:
                if st.button("✅ Oui", key="confirm_logout"):
                    st.session_state.user_id = None
                    st.session_state.username = None
                    st.session_state.is_admin = False
                    st.session_state.session_token = None
                    st.session_state.user_info = None
                    st.session_state.show_logout_confirm = False
                    st.switch_page("app.py")
            with c2:
                if st.button("❌ Non", key="cancel_logout"):
                    st.session_state.show_logout_confirm = False

        # Section d'authentification pour les utilisateurs non connectés
        if not st.session_state.user_id:
            # Titre d'authentification
            ("### 🔐 Authentification")
            
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
                
                /* Style spécial pour le bouton Mon Profil */
                .sidebar .stButton > button[key="nav_profile"] {
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
                            st.switch_page("app.py")
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
        
        # Bouton Créer un compte avec indication de page active
        current_page = _current_page_key()
        is_active = current_page == "Inscription"
        if st.button("🔐 Créer un compte", key="nav_register", help="Créer un compte", use_container_width=True, type="primary" if is_active else "secondary"):
            st.switch_page("pages/🔐_Inscription.py")

def show_welcome():
    """Affiche la section de bienvenue."""
    if st.session_state.user_id:
        # Utilisateur connecté
        stats = get_user_stats(st.session_state.user_id)
        
        st.markdown("""
        <div class="auth-container">
            <h2>🎉 Bienvenue, {} !</h2>
            <p>Vous êtes connecté à votre espace personnel de détection de fissures.</p>
        </div>
        """.format(st.session_state.username), unsafe_allow_html=True)
        
        # Espace entre le message de bienvenue et la configuration
        st.markdown("<br>", unsafe_allow_html=True)
        
        # État de la configuration
        with st.expander("🔧 État de la Configuration", expanded=False):
            st.success("✅ Système opérationnel")
            st.info("📊 Base de données connectée")
            st.info("🤖 Modèle IA chargé")
            st.info("🔐 Authentification active")
        
        # Onglets pour Présentation et Guide de Démarrage
        tab1, tab2 = st.tabs(["🚀 Présentation", "📖 Guide de Démarrage"])
        
        with tab1:
            st.markdown("""
            ### 🎯 Présentation de l'Application
            
            **Détection de Fissures** est une solution professionnelle d'inspection du béton 
            utilisant l'intelligence artificielle pour détecter et analyser les fissures 
            dans les structures en béton.
            
            #### 🔍 Fonctionnalités Principales :
            - **Détection Simple** : Analyse d'images individuelles
            - **Analyse Batch** : Traitement en lot de plusieurs images
            - **Détection Temps Réel** : Inspection via webcam
            - **Assistant IA** : Support intelligent pour vos questions
            - **Tableau de Bord** : Suivi de vos analyses
            - **Historique** : Consultation des résultats passés
            
            #### 📊 Statistiques de votre compte :
            """)
            
            # Statistiques utilisateur
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Analyses", stats['total_analyses'])
            with col2:
                st.metric("📈 Analyses Récentes", stats['recent_analyses'])
            with col3:
                st.metric("🎯 Taux de Réussite", f"{stats['success_rate']:.1f}%")
        
        with tab2:
            st.markdown("""
            ### 📖 Guide de Démarrage
            
            #### 🚀 Premiers Pas :
            1. **Détection Simple** : Commencez par analyser une image
            2. **Téléchargez** une photo de structure en béton
            3. **Lancez l'analyse** et consultez les résultats
            4. **Explorez** les autres fonctionnalités
            
            #### 🔧 Conseils d'Utilisation :
            - Utilisez des images de bonne qualité (minimum 640x480)
            - Assurez-vous que les fissures sont bien visibles
            - Évitez les reflets et ombres excessifs
            - Consultez l'historique pour suivre vos progrès
            
            #### 🎯 Actions Rapides :
            """)
            
            # Actions rapides
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Détection Simple", key="quick_simple_tab"):
                    st.switch_page("pages/🔍_Detection_Simple.py")
            with col2:
                if st.button("📊 Analyse Batch", key="quick_batch_tab"):
                    st.switch_page("pages/📊_Analyse_Batch.py")
            with col3:
                if st.button("💬 Chat Assistant", key="quick_chat_tab"):
                    st.switch_page("pages/💬_Chat_Assistant.py")
    else:
        # Utilisateur non connecté
        st.markdown("""
        <div style="background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%); padding: 2rem; border-radius: 15px; margin: 2rem 0; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2);">
            <h2 style="color: white; margin-bottom: 1rem; font-size: 2rem; font-weight: bold;">🎉 Bienvenue dans l'application</h2>
            <p style="color: white; font-size: 1.1rem; margin-bottom: 2rem;">
                Connectez-vous pour accéder à toutes les fonctionnalités avancées de notre plateforme de détection de fissures
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Espace entre le message de bienvenue et la configuration
        st.markdown("<br>", unsafe_allow_html=True)
        
        # État de la configuration
        with st.expander("🔧 État de la Configuration", expanded=False):
            st.success("✅ Système opérationnel")
            st.info("📊 Base de données connectée")
            st.info("🤖 Modèle IA chargé")
            st.warning("🔐 Authentification requise")
        
        # Présentation uniquement pour les utilisateurs non connectés
            st.markdown("""
            ### 🎯 Présentation de l'Application
            
            **Détection de Fissures** est une solution professionnelle d'inspection du béton 
            utilisant l'intelligence artificielle pour détecter et analyser les fissures 
            dans les structures en béton.
            
            #### 🔍 Fonctionnalités Principales :
            - **Détection Simple** : Analyse d'images individuelles
            - **Analyse Batch** : Traitement en lot de plusieurs images
            - **Détection Temps Réel** : Inspection via webcam
            - **Assistant IA** : Support intelligent pour vos questions
            - **Tableau de Bord** : Suivi de vos analyses
            - **Historique** : Consultation des résultats passés
            
            #### 🔐 Accès à l'application :
        """)
        
        # Section d'authentification
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Se connecter", key="welcome_login", use_container_width=True):
                st.switch_page("pages/🔑_Connexion.py")
        with col2:
            if st.button("🔐 S'inscrire", key="welcome_register", use_container_width=True):
                st.switch_page("pages/🔐_Inscription.py")

def show_features():
    """Affiche les fonctionnalités principales."""
    st.markdown("### 🚀 Fonctionnalités Principales")
    
    features = [
        {
            "icon": "🔍",
            "title": "Détection Simple",
            "description": "Analysez une image individuelle pour détecter les fissures avec notre IA avancée."
        },
        {
            "icon": "📊",
            "title": "Analyse Batch",
            "description": "Traitez plusieurs images simultanément pour des analyses en lot efficaces."
        },
        {
            "icon": "📹",
            "title": "Détection Temps Réel",
            "description": "Analysez en temps réel via votre webcam pour des inspections instantanées."
        },
        {
            "icon": "💬",
            "title": "Assistant IA",
            "description": "Posez vos questions à notre assistant intelligent spécialisé en détection de fissures."
        },
        {
            "icon": "📈",
            "title": "Tableau de Bord",
            "description": "Suivez vos analyses et consultez des statistiques détaillées de vos inspections."
        },
        {
            "icon": "📋",
            "title": "Historique",
            "description": "Consultez l'historique complet de toutes vos analyses précédentes."
        }
    ]
    
    # Affichage en grille 2x3
    col1, col2 = st.columns(2)
    
    for i, feature in enumerate(features):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 1.5rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #b56576;">
                <h4 style="color: #b56576; margin-bottom: 0.5rem;">{feature['icon']} {feature['title']}</h4>
                <p style="color: #e5e7eb; line-height: 1.5;">{feature['description']}</p>
            </div>
            """, unsafe_allow_html=True)

from utils.sidebar import show_footer

def main():
    """Fonction principale de l'application."""
    # Initialisation de la base de données
    init_database()
    
    # Affichage de la sidebar
    show_sidebar()
    
    # Affichage de l'en-tête
    show_header()
    
    # Affichage du contenu principal
    if st.session_state.current_page == "Accueil":
        show_welcome()
        st.markdown("---")
        show_features()
    
    # Affichage du footer
    show_footer()

if __name__ == "__main__":
    main()