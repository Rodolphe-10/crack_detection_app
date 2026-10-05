#!/usr/bin/env python3
"""
🛡️ Dashboard Admin
------------------

Page principale du tableau de bord administrateur.
"""

import streamlit as st
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.config import StreamlitConfig
from utils.auth import validate_session, has_permission
from utils.sidebar import show_footer


def show_dashboard_sidebar():
    """Affiche la sidebar simplifiée du dashboard admin."""

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

    
    with st.sidebar:
        # Logo en haut
        try:
            logo_path = Path("assets/images/logo_app.png")
            if logo_path.exists():
                st.image(str(logo_path), width=200, use_container_width=False)
            else:
                st.markdown("""
                <div style="text-align: center; margin: 1rem 0;">
                    <div style="background: black; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                        <span style="font-size: 60px;">🏗️</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0;">
                <div style="background: black; width: 200px; height: 200px; border-radius: 15px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
                    <span style="font-size: 60px;">🏗️</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Nom de l'app
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
            # Avatar et profil utilisateur simplifié
            st.markdown("""
            <div style="text-align: center; margin: 1rem 0; position: relative;">
                <div style="width: 60px; height: 60px; border-radius: 50%; background: #667eea; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 3px solid #1e3c72; font-size: 24px; font-weight: bold; color: white; position: relative;">
                    👤
                </div>
                <p style="margin-top: 0.5rem; font-size: 0.9rem; color: #e5e7eb; text-align: center;">{username}</p>
            </div>
            """.format(username=st.session_state.username or "Utilisateur"), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Navigation minimale
            st.markdown("### 🚀 Navigation")
            
            # Bouton Accueil
            if st.button("🏠 Accueil", key="nav_home", help="Retour à l'accueil", use_container_width=True):
                st.switch_page("app.py")
            
            # Bouton Retour
            if st.button("⬅️ Retour", key="nav_back", help="Page précédente", use_container_width=True):
                st.switch_page("app.py")
            
            st.markdown("---")
            
            # Déconnexion
            if st.button("🚪 Déconnexion", key="logout", help="Se déconnecter", use_container_width=True):
                # Nettoyer la session
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.is_admin = False
                st.session_state.session_token = None
                st.session_state.user_info = None
                st.rerun()
        
        # CSS pour le style uniforme
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
        </style>
        """, unsafe_allow_html=True)


def check_admin_authentication():
    """Vérifie l'authentification et les permissions admin."""
    if "session_token" not in st.session_state:
        st.error("❌ Accès refusé : Vous devez être connecté")
        st.stop()
    
    user_info = validate_session(st.session_state.session_token)
    if not user_info:
        st.error("❌ Session expirée. Veuillez vous reconnecter.")
        st.stop()
    
    if user_info['role'] != 'admin':
        st.error("❌ Accès refusé : Permissions administrateur requises")
        st.info("🔐 Contactez votre administrateur pour obtenir les permissions nécessaires.")
        st.stop()
    
    return user_info


def get_admin_stats():
    """Récupère les statistiques pour le dashboard admin."""
    try:
        # Connexion aux bases de données
        users_conn = sqlite3.connect("data/users.db")
        history_conn = sqlite3.connect("data/history.db")
        
        # Statistiques utilisateurs
        users_stats = users_conn.execute("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN role = 'admin' THEN 1 END) as admins,
                COUNT(CASE WHEN role != 'admin' THEN 1 END) as regular_users,
                COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as new_users_7d,
                COUNT(CASE WHEN created_at >= datetime('now', '-30 days') THEN 1 END) as new_users_30d
            FROM users
        """).fetchone()
        
        # Statistiques d'analyse
        analysis_stats = history_conn.execute("""
            SELECT 
                COUNT(*) as total_analyses,
                COUNT(CASE WHEN has_crack = 1 THEN 1 END) as cracks_found,
                COUNT(CASE WHEN has_crack = 0 THEN 1 END) as no_cracks,
                COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as analyses_7d,
                COUNT(CASE WHEN timestamp >= datetime('now', '-30 days') THEN 1 END) as analyses_30d,
                AVG(confidence) as avg_confidence
            FROM analysis_history
        """).fetchone()
        
        users_conn.close()
        history_conn.close()
        
        # Calculer le taux de succès
        success_rate = (analysis_stats[1] / analysis_stats[0] * 100) if analysis_stats[0] > 0 else 0
        
        return {
            'users': {
                'total_users': users_stats[0],
                'admins': users_stats[1],
                'regular_users': users_stats[2],
                'new_users_7d': users_stats[3],
                'new_users_30d': users_stats[4]
            },
            'analysis': {
                'total_analyses': analysis_stats[0],
                'cracks_found': analysis_stats[1],
                'no_cracks': analysis_stats[2],
                'analyses_7d': analysis_stats[3],
                'analyses_30d': analysis_stats[4],
                'avg_confidence': analysis_stats[5] or 0
            },
            'active_users': {
                'active_users_7d': users_stats[3]  # Simplifié pour l'exemple
            },
            'success_rate': success_rate
        }
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des statistiques : {e}")
        return None


def create_kpi_cards(stats):
    """Crée les cartes KPI principales en disposition horizontale."""
    if not stats:
        return
    
    st.markdown("### 📊 Indicateurs Clés de Performance")
    st.markdown("---")
    
    # Première ligne de KPIs
    st.markdown("#### 👥 Métriques Utilisateurs")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{stats['users']['total_users']}</h3>
            <p>👥 Utilisateurs Total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{stats['users']['admins']}</h3>
            <p>🛡️ Administrateurs</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Deuxième ligne de KPIs
    st.markdown("#### 🔍 Métriques d'Analyse")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{stats['analysis']['total_analyses']}</h3>
            <p>🔍 Analyses Total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        success_rate = 0
        if stats['analysis']['total_analyses'] > 0:
            success_rate = (stats['analysis']['cracks_found'] / stats['analysis']['total_analyses']) * 100
        
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{success_rate:.1f}%</h3>
            <p>🎯 Taux de Détection</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Troisième ligne de KPIs
    st.markdown("#### 📈 Activité Récente")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{stats['users']['new_users_7d']}</h3>
            <p>🆕 Nouveaux (7j)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <h3>{stats['analysis']['analyses_7d']}</h3>
            <p>📊 Analyses (7j)</p>
        </div>
        """, unsafe_allow_html=True)


def create_user_distribution_chart(stats):
    """Crée le graphique de distribution des utilisateurs par rôle."""
    if not stats:
        return
    
    # Données pour le graphique
    roles_data = {
        'Utilisateurs': stats['users']['regular_users'],
        'Administrateurs': stats['users']['admins']
    }
    
    # Créer le graphique sans titre (déjà présenté dans la section principale)
    fig = px.pie(
        values=list(roles_data.values()),
        names=list(roles_data.keys()),
        color_discrete_sequence=['#1e3c72', '#667eea']
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=14,
        textfont_color='white'
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_analysis_trend_chart():
    """Crée le graphique des tendances d'analyse."""
    try:
        # Récupérer les données d'analyse des 30 derniers jours
        conn = sqlite3.connect("data/history.db")
        
        # Données par jour
        daily_data = pd.read_sql_query("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_analyses,
                COUNT(CASE WHEN has_crack = 1 THEN 1 END) as cracks_found,
                AVG(confidence) as avg_confidence
            FROM analysis_history 
            WHERE timestamp >= datetime('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, conn)
        
        conn.close()
        
        if daily_data.empty:
            st.info("📊 Aucune donnée d'analyse disponible pour les 30 derniers jours")
            return
        
        # Créer le graphique
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('📈 Analyses par Jour', '🎯 Taux de Détection'),
            vertical_spacing=0.1
        )
        
        # Graphique des analyses totales
        fig.add_trace(
            go.Scatter(
                x=daily_data['date'],
                y=daily_data['total_analyses'],
                mode='lines+markers',
                name='Analyses Total',
                line=dict(color='#1e3c72', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Graphique du taux de détection
        daily_data['detection_rate'] = (daily_data['cracks_found'] / daily_data['total_analyses']) * 100
        
        fig.add_trace(
            go.Scatter(
                x=daily_data['date'],
                y=daily_data['detection_rate'],
                mode='lines+markers',
                name='Taux de Détection (%)',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=40, r=40, t=40, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Améliorer les axes
        fig.update_xaxes(
            title_text="Date", 
            row=2, 
            col=1,
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        )
        fig.update_yaxes(
            title_text="Nombre d'Analyses", 
            row=1, 
            col=1,
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        )
        fig.update_yaxes(
            title_text="Taux de Détection (%)", 
            row=2, 
            col=1,
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.1)'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la création du graphique : {e}")


def create_recent_activity_section():
    """Affiche la section d'activité récente avec une meilleure disposition."""
    
    try:
        # Connexions récentes
        conn = sqlite3.connect("data/users.db")
        
        # Simulation des connexions récentes (car login_logs n'existe pas)
        recent_logins = pd.DataFrame({
            'username': [],
            'first_name': [],
            'last_name': [],
            'role': [],
            'success': [],
            'created_at': [],
            'ip_address': []
        })
        
        # Analyses récentes
        history_conn = sqlite3.connect("data/history.db")
        
        recent_analyses = pd.read_sql_query("""
            SELECT 
                page,
                method,
                has_crack as crack_detected,
                confidence as confidence_score,
                filename,
                timestamp as created_at
            FROM analysis_history
            ORDER BY timestamp DESC
            LIMIT 10
        """, history_conn)
        
        conn.close()
        history_conn.close()
        
        # Disposition en colonnes avec plus d'espacement
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔐 Connexions Récentes")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not recent_logins.empty:
                for _, login in recent_logins.iterrows():
                    status_icon = "✅" if login['success'] else "❌"
                    status_color = "green" if login['success'] else "red"
                    
                    st.markdown(f"""
                    <div class="activity-card" style="border-left-color: {status_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{login['first_name']} {login['last_name']}</strong> ({login['username']})
                                <br>
                                <small style="opacity: 0.7;">{login['role']} • {login['ip_address']}</small>
                            </div>
                            <div style="text-align: right;">
                                <span style="color: {status_color}; font-size: 1.2rem;">{status_icon}</span>
                                <br>
                                <small style="opacity: 0.7;">{login['created_at']}</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📊 Aucune connexion récente disponible")
        
        with col2:
            st.markdown("#### 🔍 Analyses Récentes")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not recent_analyses.empty:
                for _, analysis in recent_analyses.iterrows():
                    crack_icon = "🔴" if analysis['crack_detected'] else "🟢"
                    crack_text = "Fissure détectée" if analysis['crack_detected'] else "Aucune fissure"
                    
                    st.markdown(f"""
                    <div class="activity-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>{analysis['page']}</strong> ({analysis['method']})
                                <br>
                                <small style="opacity: 0.7;">{analysis['filename']}</small>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 1.2rem;">{crack_icon}</span>
                                <br>
                                <small style="opacity: 0.7;">{crack_text} ({analysis['confidence_score']:.1f}%)</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📊 Aucune analyse récente disponible")
                
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération de l'activité récente : {e}")


def main():
    """Fonction principale du dashboard admin."""
    # Configuration de la page
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    
    # CSS global pour améliorer la présentation
    st.markdown("""
    <style>
    /* CSS global pour le dashboard */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px !important;
    }
    
    /* Amélioration des titres avec plus d'espacement */
    .main h1 {
        margin-bottom: 2rem !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        text-align: center !important;
    }
    
    .main h2 {
        margin-bottom: 1.5rem !important;
        font-weight: 600 !important;
        font-size: 2rem !important;
        color: #1e3c72 !important;
        border-bottom: 2px solid #1e3c72 !important;
        padding-bottom: 0.5rem !important;
    }
    
    .main h3 {
        margin-bottom: 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        color: #ffffff !important;
        margin-top: 2rem !important;
    }
    
    .main h4 {
        margin-bottom: 1rem !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        color: #667eea !important;
        margin-top: 1.5rem !important;
    }
    
    .main h5 {
        margin-bottom: 0.8rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        color: #e5e7eb !important;
        margin-top: 1rem !important;
    }
    
    /* Espacement des sections */
    .main .stMarkdown {
        margin-bottom: 2rem !important;
    }
    
    /* Amélioration des séparateurs */
    .main hr {
        margin: 3rem 0 !important;
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent, #1e3c72, transparent) !important;
    }
    
    /* Style des cartes KPI avec plus d'espacement */
    .kpi-card {
        background: linear-gradient(135deg, #1e3c72 0%, #667eea 100%);
        padding: 2.5rem !important;
        border-radius: 15px;
        text-align: center;
        color: white;
        box-shadow: 0 8px 32px rgba(30, 60, 114, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin: 1rem 0 !important;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(30, 60, 114, 0.4);
    }
    
    .kpi-card h3 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem !important;
    }
    
    .kpi-card p {
        margin: 0;
        opacity: 0.9;
        font-size: 1.1rem;
        font-weight: 500;
    }
    
    /* Amélioration des graphiques avec plus d'espacement */
    .main .stPlotlyChart {
        margin: 2rem 0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
    }
    
    /* Style des statistiques détaillées avec plus d'espacement */
    .stats-section {
        background: rgba(255,255,255,0.05);
        padding: 2.5rem !important;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
        margin: 1.5rem 0 !important;
    }
    
    .stats-section h4 {
        color: #1e3c72;
        margin-bottom: 1.5rem !important;
        font-weight: 600;
    }
    
    .stats-section ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .stats-section li {
        padding: 0.8rem 0 !important;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 1.1rem !important;
    }
    
    .stats-section li:last-child {
        border-bottom: none;
    }
    
    .stats-section strong {
        color: #1e3c72;
        font-weight: 600;
    }
    
    /* Amélioration de l'activité récente avec plus d'espacement */
    .activity-card {
        background: rgba(255,255,255,0.05);
        padding: 2rem !important;
        border-radius: 12px;
        margin: 1.5rem 0 !important;
        border-left: 4px solid #1e3c72;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease;
    }
    
    .activity-card:hover {
        transform: translateX(5px);
    }
    
    /* Espacement supplémentaire entre les colonnes */
    .row-widget.stHorizontal {
        gap: 2rem !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 1rem !important;
        }
        
        .kpi-card {
            padding: 1.5rem !important;
        }
        
        .kpi-card h3 {
            font-size: 2rem;
        }
        
        .stats-section {
            padding: 1.5rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Affichage de la sidebar personnalisée du dashboard
    show_dashboard_sidebar()
    
    # Vérification de l'authentification admin
    admin_user = check_admin_authentication()
    
    # En-tête du dashboard
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #667eea 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">🛡️ Dashboard Administrateur</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">
            Bienvenue, {admin_user['first_name']} {admin_user['last_name']} | Dernière connexion : {datetime.now().strftime('%d/%m/%Y %H:%M')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Récupération des statistiques
    with st.spinner("🔄 Chargement des statistiques..."):
        stats = get_admin_stats()
    
    if stats:
        # Affichage des KPIs
        create_kpi_cards(stats)
        
        st.markdown("---")
        
        # Section des graphiques avec meilleur espacement
        st.markdown("### 📈 Visualisations et Statistiques")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Graphiques en disposition horizontale
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Distribution des Utilisateurs")
            create_user_distribution_chart(stats)
        
        with col2:
            st.markdown("#### 📋 Statistiques Détaillées")
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Statistiques utilisateurs
            st.markdown("##### 👥 Utilisateurs")
            user_stats = stats['users']
            st.markdown(f"""
            <div class="stats-section">
                <ul>
                    <li><strong>Total :</strong> {user_stats['total_users']}</li>
                    <li><strong>Nouveaux (7j) :</strong> {user_stats['new_users_7d']}</li>
                    <li><strong>Nouveaux (30j) :</strong> {user_stats['new_users_30d']}</li>
                    <li><strong>Utilisateurs :</strong> {user_stats['regular_users']}</li>
                    <li><strong>Administrateurs :</strong> {user_stats['admins']}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Statistiques d'analyse
            st.markdown("##### 🔍 Analyses")
            analysis_stats = stats['analysis']
            st.markdown(f"""
            <div class="stats-section">
                <ul>
                    <li><strong>Total :</strong> {analysis_stats['total_analyses']}</li>
                    <li><strong>Fissures détectées :</strong> {analysis_stats['cracks_found']}</li>
                    <li><strong>Aucune fissure :</strong> {analysis_stats['no_cracks']}</li>
                    <li><strong>Analyses (7j) :</strong> {analysis_stats['analyses_7d']}</li>
                    <li><strong>Analyses (30j) :</strong> {analysis_stats['analyses_30d']}</li>
                    <li><strong>Confiance moyenne :</strong> {analysis_stats['avg_confidence']:.1f}%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Graphique des tendances avec plus d'espacement
        st.markdown("### 📊 Tendances d'Analyse")
        st.markdown("<br>", unsafe_allow_html=True)
        create_analysis_trend_chart()
        
        st.markdown("---")
        
        # Activité récente avec plus d'espacement
        st.markdown("### 🔄 Activité Récente")
        st.markdown("<br>", unsafe_allow_html=True)
        create_recent_activity_section()
        
    else:
        st.error("❌ Impossible de charger les statistiques du dashboard")
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()
