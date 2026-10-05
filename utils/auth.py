#!/usr/bin/env python3
"""
Système d'authentification
-------------------------

Gestion des utilisateurs, authentification, sessions et rôles.
"""

import hashlib
import secrets
import sqlite3
import threading
import time
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import streamlit as st


# Configuration
_DB_DIR = Path(__file__).parent.parent / "data"
_DB_PATH = _DB_DIR / "users.db"
_INIT_LOCK = threading.Lock()

# Rôles disponibles
ROLES = {
    "client": "Client",
    "inspector": "Inspecteur", 
    "expert": "Expert",
    "admin": "Administrateur"
}

# Permissions par rôle
PERMISSIONS = {
    "client": ["simple_analysis", "view_own_history"],
    "inspector": ["simple_analysis", "realtime_analysis", "batch_analysis", "view_own_history", "export_reports"],
    "expert": ["simple_analysis", "realtime_analysis", "batch_analysis", "view_all_history", "export_reports", "validate_analyses"],
    "admin": ["*"]  # Toutes les permissions
}


def _ensure_db() -> None:
    """Crée la base de données utilisateurs si nécessaire."""
    if not _DB_DIR.exists():
        _DB_DIR.mkdir(parents=True, exist_ok=True)

    with _INIT_LOCK:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(64) NOT NULL,
                    first_name VARCHAR(50) NOT NULL,
                    last_name VARCHAR(50) NOT NULL,
                    profile_photo BLOB,
                    avatar_color VARCHAR(7) DEFAULT '#667eea',
                    avatar_letter CHAR(1),
                    role VARCHAR(20) DEFAULT 'client',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)
            
            # Table des sessions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(128) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Table des logs de connexion
            conn.execute("""
                CREATE TABLE IF NOT EXISTS login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username VARCHAR(50),
                    action VARCHAR(20) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()


def _hash_password(password: str, salt: str) -> str:
    """Hache un mot de passe avec un salt."""
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()


def _generate_salt() -> str:
    """Génère un salt aléatoire."""
    return secrets.token_hex(32)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe selon les critères de sécurité.
    
    Critères requis :
    - Au moins 8 caractères
    - Au moins 3 caractères spéciaux
    - Au moins une majuscule
    - Au moins une minuscule
    - Au moins un chiffre
    
    Args:
        password (str): Le mot de passe à valider
        
    Returns:
        tuple[bool, str]: (is_valid, message)
    """
    if not password:
        return False, "Le mot de passe est requis"
    
    # Vérifier la longueur minimale
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    # Vérifier au moins une majuscule
    if not any(c.isupper() for c in password):
        return False, "Le mot de passe doit contenir au moins une majuscule"
    
    # Vérifier au moins une minuscule
    if not any(c.islower() for c in password):
        return False, "Le mot de passe doit contenir au moins une minuscule"
    
    # Vérifier au moins un chiffre
    if not any(c.isdigit() for c in password):
        return False, "Le mot de passe doit contenir au moins un chiffre"
    
    # Vérifier au moins 3 caractères spéciaux
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    special_count = sum(1 for c in password if c in special_chars)
    if special_count < 3:
        return False, f"Le mot de passe doit contenir au moins 3 caractères spéciaux ({special_count}/3 trouvés). Caractères acceptés : {special_chars}"
    
    return True, "Mot de passe valide"


def _generate_session_token() -> str:
    """Génère un token de session sécurisé."""
    return secrets.token_urlsafe(64)


def register_user(
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "inspector",
    profile_photo: Optional[bytes] = None
) -> Dict[str, Any]:
    """Enregistre un nouvel utilisateur."""
    _ensure_db()
    
    # Validation des données
    if not username or not email or not password or not first_name or not last_name:
        return {"success": False, "error": "Tous les champs sont requis"}
    
    # Valider la force du mot de passe
    is_valid, error_msg = validate_password_strength(password)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    if role not in ROLES:
        return {"success": False, "error": "Rôle invalide"}
    
    # Générer avatar
    avatar_letter = first_name[0].upper()
    avatar_color = f"#{secrets.token_hex(3)}"  # Couleur aléatoire
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Vérifier si l'utilisateur existe déjà
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            ).fetchone()
            
            if existing:
                return {"success": False, "error": "Nom d'utilisateur ou email déjà utilisé"}
            
            # Créer l'utilisateur
            salt = _generate_salt()
            password_hash = _hash_password(password, salt)
            
            cursor = conn.execute("""
                INSERT INTO users (
                    username, email, password_hash, salt, first_name, last_name,
                    profile_photo, avatar_color, avatar_letter, role
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, email, password_hash, salt, first_name, last_name,
                profile_photo, avatar_color, avatar_letter, role
            ))
            
            user_id = cursor.lastrowid
            
            # Log de création
            conn.execute("""
                INSERT INTO login_logs (user_id, username, action, success)
                VALUES (?, ?, 'register', 1)
            """, (user_id, username))
            
            conn.commit()
            
            return {
                "success": True,
                "user_id": user_id,
                "message": "Utilisateur créé avec succès"
            }
            
    except Exception as e:
        return {"success": False, "error": f"Erreur lors de la création: {str(e)}"}


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    """Authentifie un utilisateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Récupérer l'utilisateur
            user = conn.execute("""
                SELECT id, username, password_hash, salt, first_name, last_name,
                       role, is_active, login_attempts, locked_until
                FROM users WHERE username = ? OR email = ?
            """, (username, username)).fetchone()
            
            if not user:
                _log_login_attempt(None, username, "login", False)
                return {"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect"}
            
            user_id, db_username, db_hash, db_salt, first_name, last_name, role, is_active, attempts, locked_until = user
            
            # Vérifier si le compte est verrouillé
            if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                return {"success": False, "error": "Compte temporairement verrouillé"}
            
            # Vérifier si le compte est actif
            if not is_active:
                return {"success": False, "error": "Compte désactivé"}
            
            # Vérifier le mot de passe
            if _hash_password(password, db_salt) != db_hash:
                # Incrémenter les tentatives
                new_attempts = attempts + 1
                if new_attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                    conn.execute("""
                        UPDATE users SET login_attempts = ?, locked_until = ?
                        WHERE id = ?
                    """, (new_attempts, locked_until, user_id))
                else:
                    conn.execute("""
                        UPDATE users SET login_attempts = ? WHERE id = ?
                    """, (new_attempts, user_id))
                
                conn.commit()
                _log_login_attempt(user_id, username, "login", False)
                return {"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect"}
            
            # Réinitialiser les tentatives
            conn.execute("""
                UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id,))
            
            # Créer une session
            session_token = _generate_session_token()
            expires_at = (datetime.now() + timedelta(days=7)).isoformat()
            
            conn.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, session_token, expires_at))
            
            conn.commit()
            
            # Log de connexion réussie
            _log_login_attempt(user_id, username, "login", True)
            
            return {
                "success": True,
                "session_token": session_token,
                "user": {
                    "id": user_id,
                    "username": db_username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role
                }
            }
            
    except Exception as e:
        return {"success": False, "error": f"Erreur d'authentification: {str(e)}"}


def validate_session(session_token: str) -> Optional[Dict[str, Any]]:
    """Valide un token de session et retourne les infos utilisateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Récupérer la session
            session = conn.execute("""
                SELECT s.user_id, s.expires_at, u.username, u.first_name, u.last_name, u.role, u.is_active
                FROM user_sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ?
            """, (session_token,)).fetchone()
            
            if not session:
                return None
            
            user_id, expires_at, username, first_name, last_name, role, is_active = session
            
            # Vérifier l'expiration
            if datetime.fromisoformat(expires_at) < datetime.now():
                # Supprimer la session expirée
                conn.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
                conn.commit()
                return None
            
            # Vérifier si l'utilisateur est actif
            if not is_active:
                return None
            
            return {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "role": role
            }
            
    except Exception:
        return None


def logout_user(session_token: str) -> bool:
    """Déconnecte un utilisateur en supprimant sa session."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            conn.commit()
            return True
    except Exception:
        return False


def get_user_info(user_id: int) -> Optional[Dict[str, Any]]:
    """Récupère les informations d'un utilisateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            user = conn.execute("""
                SELECT id, username, email, first_name, last_name, profile_photo,
                       avatar_color, avatar_letter, role, created_at, last_login
                FROM users WHERE id = ?
            """, (user_id,)).fetchone()
            
            if not user:
                return None
            
            profile_photo_base64 = None
            if user[5]: # profile_photo is at index 5
                profile_photo_base64 = base64.b64encode(user[5]).decode('utf-8')

            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4],
                "profile_photo": profile_photo_base64,
                "avatar_color": user[6],
                "avatar_letter": user[7],
                "role": user[8],
                "created_at": user[9],
                "last_login": user[10]
            }
    except Exception:
        return None


def update_user_profile(
    user_id: int,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    profile_photo: bytes = None
) -> Dict[str, Any]:
    """Met à jour le profil d'un utilisateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
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
            if profile_photo is not None:
                updates.append("profile_photo = ?")
                params.append(profile_photo)
            
            if not updates:
                return {"success": False, "error": "Aucune modification"}
            
            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            conn.execute(query, params)
            conn.commit()
            
            return {"success": True, "message": "Profil mis à jour"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur de mise à jour: {str(e)}"}


def change_password(user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
    """Change le mot de passe d'un utilisateur."""
    _ensure_db()
    
    # Valider la force du nouveau mot de passe
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Vérifier l'ancien mot de passe
            user = conn.execute("SELECT password_hash, salt FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "error": "Utilisateur non trouvé"}
            
            db_hash, db_salt = user
            if _hash_password(current_password, db_salt) != db_hash:
                return {"success": False, "error": "Mot de passe actuel incorrect"}
            
            # Générer nouveau hash
            new_salt = _generate_salt()
            new_hash = _hash_password(new_password, new_salt)
            
            # Mettre à jour
            conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, new_salt, user_id))
            conn.commit()
            
            return {"success": True, "message": "Mot de passe changé avec succès"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur: {str(e)}"}


def _log_login_attempt(user_id: Optional[int], username: str, action: str, success: bool) -> None:
    """Enregistre une tentative de connexion."""
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute("""
                INSERT INTO login_logs (user_id, username, action, success)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, action, success))
            conn.commit()
    except Exception:
        pass  # Ignorer les erreurs de logging


def has_permission(user_role: str, permission: str) -> bool:
    """Vérifie si un rôle a une permission donnée."""
    if user_role not in PERMISSIONS:
        return False
    
    user_permissions = PERMISSIONS[user_role]
    return "*" in user_permissions or permission in user_permissions


def update_user_by_admin(
    user_id: int,
    first_name: str = None,
    last_name: str = None,
    email: str = None,
    role: str = None,
    is_active: bool = None
) -> Dict[str, Any]:
    """Met à jour un utilisateur par un administrateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
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
            conn.execute(query, params)
            conn.commit()
            
            return {"success": True, "message": "Utilisateur mis à jour avec succès"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur de mise à jour: {str(e)}"}


def delete_user(user_id: int) -> Dict[str, Any]:
    """Supprime un utilisateur."""
    _ensure_db()
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Vérifier que l'utilisateur existe
            user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "error": "Utilisateur non trouvé"}
            
            # Supprimer l'utilisateur
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            return {"success": True, "message": f"Utilisateur {user[0]} supprimé avec succès"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur de suppression: {str(e)}"}


def reset_user_password(user_id: int, new_password: str) -> Dict[str, Any]:
    """Réinitialise le mot de passe d'un utilisateur par un administrateur."""
    _ensure_db()
    
    # Valider la force du nouveau mot de passe
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        return {"success": False, "error": error_msg}
    
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            # Vérifier que l'utilisateur existe
            user = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
            if not user:
                return {"success": False, "error": "Utilisateur non trouvé"}
            
            # Générer nouveau hash
            new_salt = _generate_salt()
            new_hash = _hash_password(new_password, new_salt)
            
            # Mettre à jour
            conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (new_hash, new_salt, user_id))
            conn.commit()
            
            return {"success": True, "message": f"Mot de passe de {user[0]} réinitialisé avec succès"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur: {str(e)}"}


# Initialisation
_ensure_db()
