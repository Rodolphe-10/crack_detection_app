#!/usr/bin/env python3
"""
👥 Gestion Utilisateurs
-----------------------

Page de gestion des utilisateurs pour les administrateurs.
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

from config.config import StreamlitConfig
from utils.auth import validate_session, has_permission, ROLES, validate_password_strength
from utils.sidebar import show_unified_sidebar, show_footer


def check_admin_authentication():
    """Vérifie l'authentification et les permissions admin."""
    if "session_token" not in st.session_state:
        st.error("❌ Accès refusé : Vous devez être connecté")
        st.stop()
    
    user_info = validate_session(st.session_state.session_token)
    if not user_info:
        st.error("❌ Session expirée. Veuillez vous reconnecter.")
        st.stop()
    
    if not has_permission(user_info['role'], "admin_access"):
        st.error("❌ Accès refusé : Permissions administrateur requises")
        st.info("🔐 Contactez votre administrateur pour obtenir les permissions nécessaires.")
        st.stop()
    
    return user_info


def get_users_data():
    """Récupère les données des utilisateurs."""
    try:
        conn = sqlite3.connect("data/users.db")
        
        query = """
            SELECT 
                u.id,
                u.username,
                u.email,
                u.first_name,
                u.last_name,
                u.role,
                u.created_at,
                u.last_login,
                u.is_active
            FROM users u
            ORDER BY u.created_at DESC
        """
        
        users_df = pd.read_sql_query(query, conn)
        conn.close()
        
        return users_df
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des utilisateurs : {e}")
        return pd.DataFrame()


def display_users_table(users_df):
    """Affiche le tableau des utilisateurs."""
    if users_df.empty:
        st.info("📊 Aucun utilisateur trouvé")
        return
    
    st.markdown("### 👥 Liste des Utilisateurs")
    
    for _, user in users_df.iterrows():
        with st.expander(f"👤 {user['first_name']} {user['last_name']} ({user['username']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Informations :**
                - **Nom :** {user['first_name']} {user['last_name']}
                - **Username :** {user['username']}
                - **Email :** {user['email']}
                - **Rôle :** {ROLES.get(user['role'], user['role'])}
                - **Statut :** {'🟢 Actif' if user['is_active'] else '🔴 Inactif'}
                """)
            
            with col2:
                st.markdown(f"""
                **Dates :**
                - **Créé le :** {user['created_at']}
                - **Dernière connexion :** {user['last_login'] or 'Jamais'}
                """)
            
            # Actions
            st.markdown("---")
            st.markdown("### ⚙️ Actions")
            
            # Onglets pour les actions
            action_tab1, action_tab2, action_tab3 = st.tabs(["✏️ Modifier", "🔐 Réinitialiser MDP", "🗑️ Supprimer"])
            
            with action_tab1:
                st.markdown("#### ✏️ Modifier l'utilisateur")
                with st.form(f"edit_user_{user['id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_first_name = st.text_input("Prénom", value=user['first_name'], key=f"first_name_{user['id']}")
                        new_email = st.text_input("Email", value=user['email'], key=f"email_{user['id']}")
                    
                    with col2:
                        new_last_name = st.text_input("Nom", value=user['last_name'], key=f"last_name_{user['id']}")
                        new_role = st.selectbox(
                            "Rôle",
                            options=list(ROLES.keys()),
                            index=list(ROLES.keys()).index(user['role']) if user['role'] in ROLES else 0,
                            format_func=lambda x: ROLES[x],
                            key=f"role_{user['id']}"
                        )
                        new_is_active = st.checkbox("Compte actif", value=user['is_active'], key=f"active_{user['id']}")
                    
                    if st.form_submit_button("💾 Sauvegarder les modifications"):
                        result = update_user_by_admin(
                            user_id=user['id'],
                            first_name=new_first_name,
                            last_name=new_last_name,
                            email=new_email,
                            role=new_role,
                            is_active=new_is_active
                        )
                        
                        if result["success"]:
                            st.success("✅ Utilisateur modifié avec succès")
                            st.rerun()
                        else:
                            st.error(f"❌ Erreur : {result['error']}")
            
            with action_tab2:
                st.markdown("#### 🔐 Réinitialiser le mot de passe")
                with st.form(f"reset_password_{user['id']}"):
                    new_password = st.text_input("Nouveau mot de passe", type="password", key=f"new_pass_{user['id']}")
                    confirm_password = st.text_input("Confirmer le mot de passe", type="password", key=f"confirm_pass_{user['id']}")
                    
                    if st.form_submit_button("🔐 Réinitialiser le mot de passe"):
                        if not new_password or not confirm_password:
                            st.error("❌ Veuillez remplir tous les champs")
                        elif new_password != confirm_password:
                            st.error("❌ Les mots de passe ne correspondent pas")
                        else:
                            # Validation de la force du mot de passe
                            is_valid, error_msg = validate_password_strength(new_password)
                            if not is_valid:
                                st.error(f"❌ {error_msg}")
                            else:
                                result = reset_user_password(user['id'], new_password)
                                if result["success"]:
                                    st.success("✅ Mot de passe réinitialisé avec succès")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Erreur : {result['error']}")
            
            with action_tab3:
                st.markdown("#### 🗑️ Supprimer l'utilisateur")
                st.warning(f"⚠️ **Attention :** Cette action est irréversible !")
                st.info(f"Vous êtes sur le point de supprimer l'utilisateur **{user['first_name']} {user['last_name']}** ({user['username']})")
                
                # Confirmation de suppression
                confirm_delete = st.checkbox(f"Je confirme vouloir supprimer {user['username']}", key=f"confirm_delete_{user['id']}")
                
                if confirm_delete:
                    if st.button("🗑️ Supprimer définitivement", type="primary", key=f"delete_{user['id']}"):
                        result = delete_user(user['id'])
                        if result["success"]:
                            st.success("✅ Utilisateur supprimé avec succès")
                            st.rerun()
                        else:
                            st.error(f"❌ Erreur : {result['error']}")


def update_user_by_admin(user_id: int, first_name: str = None, last_name: str = None, email: str = None, role: str = None, is_active: bool = None):
    """Met à jour un utilisateur par un administrateur."""
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if first_name is not None:
            updates.append("first_name = ?")
            params.append(first_name)
        if last_name is not None:
            updates.append("last_name = ?")
            params.append(last_name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if role is not None:
            if role not in ROLES:
                return {"success": False, "error": "Rôle invalide"}
            updates.append("role = ?")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            return {"success": False, "error": "Aucune modification"}
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Utilisateur mis à jour avec succès"}
        
    except Exception as e:
        return {"success": False, "error": f"Erreur de mise à jour: {str(e)}"}


def delete_user(user_id: int):
    """Supprime un utilisateur."""
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        
        # Vérifier que l'utilisateur existe
        user = cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return {"success": False, "error": "Utilisateur non trouvé"}
        
        # Supprimer l'utilisateur
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Utilisateur {user[0]} supprimé avec succès"}
        
    except Exception as e:
        return {"success": False, "error": f"Erreur de suppression: {str(e)}"}


def reset_user_password(user_id: int, new_password: str):
    """Réinitialise le mot de passe d'un utilisateur par un administrateur."""
    if len(new_password) < 8:
        return {"success": False, "error": "Le mot de passe doit contenir au moins 8 caractères"}
    
    try:
        conn = sqlite3.connect("data/users.db")
        cursor = conn.cursor()
        
        # Vérifier que l'utilisateur existe
        user = cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return {"success": False, "error": "Utilisateur non trouvé"}
        
        # Générer nouveau hash avec la même méthode que l'app
        import hashlib
        import secrets
        salt = secrets.token_hex(32)
        new_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000).hex()
        
        # Mettre à jour
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, salt, user_id))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Mot de passe de {user[0]} réinitialisé avec succès"}
        
    except Exception as e:
        return {"success": False, "error": f"Erreur: {str(e)}"}


def create_user_management_form():
    """Formulaire de création d'utilisateur."""
    st.markdown("### ➕ Créer un Nouvel Utilisateur")
    
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("Prénom *", placeholder="Prénom")
            email = st.text_input("Email *", placeholder="email@exemple.com")
            username = st.text_input("Nom d'utilisateur *", placeholder="nom_utilisateur")
        
        with col2:
            last_name = st.text_input("Nom *", placeholder="Nom")
            role = st.selectbox(
                "Rôle *",
                options=list(ROLES.keys()),
                format_func=lambda x: ROLES[x]
            )
            is_active = st.checkbox("Compte actif", value=True)
        
        password = st.text_input("Mot de passe *", type="password", placeholder="Mot de passe")
        confirm_password = st.text_input("Confirmer le mot de passe *", type="password", placeholder="Confirmez le mot de passe")
        
        submitted = st.form_submit_button("🚀 Créer l'utilisateur")
        
        if submitted:
            if not all([first_name, last_name, email, username, password, confirm_password]):
                st.error("❌ Tous les champs marqués d'un * sont obligatoires")
                return
            
            if password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
                return
            
            # Créer l'utilisateur
            from utils.auth import register_user
            result = register_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            if result["success"]:
                st.success("✅ Utilisateur créé avec succès")
                st.rerun()
            else:
                st.error(f"❌ Erreur lors de la création : {result['error']}")


def main():
    """Fonction principale de la gestion des utilisateurs."""
    # Configuration de la page
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    
    # Affichage de la sidebar unifiée
    show_unified_sidebar("Gestion Utilisateurs")
    


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


    
    # Vérification de l'authentification admin
    admin_user = check_admin_authentication()
    
    # En-tête
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">👥 Gestion des Utilisateurs</h1>
        <p style="color: white; margin: 0.5rem 0 0 0; text-align: center; opacity: 0.9;">
            Administration des comptes utilisateurs
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Onglets
    tab1, tab2 = st.tabs(["📋 Liste des Utilisateurs", "➕ Créer Utilisateur"])
    
    with tab1:
        # Récupération des données
        users_df = get_users_data()
        
        # Affichage du tableau
        display_users_table(users_df)
    
    with tab2:
        # Formulaire de création
        create_user_management_form()
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()
