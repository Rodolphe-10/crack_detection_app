#!/usr/bin/env python3
"""
Configuration générale de l'application
======================================

Ce module contient toutes les configurations
pour l'application de détection de fissures.
"""

import os
from pathlib import Path

class AppConfig:
    """Configuration principale de l'application."""
    
    # Informations de l'application
    APP_TITLE = "🏗️ Détection de Fissures"
    APP_SUBTITLE = "Solution Professionnelle pour l'Inspection du Béton"
    
    # Chemins des modèles
    BASE_DIR = Path(__file__).parent.parent
    MODELS_DIR = BASE_DIR / "models"
    CLASSIFICATION_MODEL_PATH = MODELS_DIR / "classification" / "best_classification_model.pth"
    SEGMENTATION_MODEL_PATH = MODELS_DIR / "segmentation" / "best_unet_model.pth"
    
    # Configuration des modèles
    CLASSIFICATION_CLASSES = ["Non-fissuré", "Fissuré"]
    SEGMENTATION_CLASSES = ["Background", "Fissure"]
    IMAGE_SIZE = 224
    DEVICE = "cpu"  # Sera détecté automatiquement
    
    # Seuils par défaut
    DEFAULT_CLASSIFICATION_THRESHOLD = 0.7
    DEFAULT_SEGMENTATION_THRESHOLD = 0.5
    MIN_CONTOUR_AREA = 100  # Pixels minimum pour une fissure valide
    
    # Configuration de l'interface
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
    ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    MAX_BATCH_SIZE = 20
    
    # Couleurs du thème noir
    COLORS = {
        'primary': '#ffffff',      # Blanc pour le texte principal
        'secondary': '#333333',    # Gris foncé
        'accent': '#ff6b35',       # Orange pour les accents
        'success': '#28a745',      # Vert - structure saine
        'danger': '#dc3545',       # Rouge - fissures critiques
        'warning': '#ffc107',      # Jaune - attention
        'background': '#000000',   # Fond noir
        'text': '#ffffff',         # Texte blanc
        'muted': '#cccccc'         # Texte secondaire gris clair
    }
    
    # Classes de classification
    CLASSIFICATION_CLASSES = {
        0: "Pas de fissure",
        1: "Fissure détectée"
    }
    
    # Configuration des visualisations
    MASK_COLORS = {
        'crack': (255, 0, 0),      # Rouge pour les fissures
        'overlay_alpha': 0.6       # Transparence des overlays
    }
    
    # Métriques des modèles (à jour avec nos résultats)
    MODEL_METRICS = {
        'classification': {
            'accuracy': 87.93,
            'precision': 88.81,
            'recall': 86.80,
            'f1_score': 87.80
        },
        'segmentation': {
            'dice_score': 0.85,  # À ajuster selon nos résultats
            'iou': 0.78          # À ajuster selon nos résultats
        }
    }
    
    # Configuration de l'historique
    HISTORY_FILE = BASE_DIR / "data" / "analysis_history.json"
    MAX_HISTORY_ENTRIES = 1000
    
    # Messages et textes
    MESSAGES = {
        'upload_help': "Glissez-déposez vos images ici ou cliquez pour parcourir",
        'processing': "Analyse en cours...",
        'no_crack_detected': "✅ Aucune fissure détectée",
        'crack_detected': "⚠️ Fissure détectée",
        'analysis_complete': "Analyse terminée",
        'error_loading_model': "Erreur lors du chargement du modèle",
        'error_processing_image': "Erreur lors du traitement de l'image"
    }

class StreamlitConfig:
    """Configuration spécifique à Streamlit."""
    
    # Configuration de la page
    PAGE_CONFIG = {
        "page_title": "Détection de Fissures",
        "page_icon": "🏗️",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # Style CSS personnalisé - Thème Noir Simple
    CUSTOM_CSS = """
    <style>
    /* Thème noir simple */
    .stApp {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    .main-header {
        background: #111111;
        color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #333333;
    }
    
    .content-card {
        background: #111111;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #333333;
    }
    
    /* Sidebar complètement noir */
    .css-1d391kg, .css-1lcbmhc, .css-1y0tads, .st-emotion-cache-1lcbmhc, .st-emotion-cache-1d391kg {
        background-color: #000000 !important;
    }
    
    /* Navigation sidebar noir */
    .css-1rs6os .css-17ziqus, .st-emotion-cache-17ziqus {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    
    /* Liens navigation en blanc */
    .css-1rs6os .css-17ziqus a, .st-emotion-cache-17ziqus a {
        color: #ffffff !important;
    }
    
    /* Liens actifs */
    .css-1rs6os .css-17ziqus a:hover, .st-emotion-cache-17ziqus a:hover {
        background-color: #333333 !important;
        color: #ffffff !important;
    }
    
    /* Texte blanc */
    h1, h2, h3, h4, h5, h6, p, div, span {
        color: #ffffff !important;
    }
    
    /* Forcer la sidebar en noir */
    section[data-testid="stSidebar"] {
        background-color: #000000 !important;
    }
    
    /* Navigation pages en noir */
    section[data-testid="stSidebar"] > div {
        background-color: #000000 !important;
    }
    
    /* Masquer le menu de navigation par défaut de Streamlit */
    .css-1v3fvcr, .css-1rs6os, .css-17ziqus, .st-emotion-cache-1v3fvcr, .st-emotion-cache-1rs6os, .st-emotion-cache-17ziqus {
        display: none !important;
    }
    
    /* Masquer le menu de navigation des pages */
    section[data-testid="stSidebar"] .css-1v3fvcr,
    section[data-testid="stSidebar"] .css-1rs6os,
    section[data-testid="stSidebar"] .css-17ziqus,
    section[data-testid="stSidebar"] .st-emotion-cache-1v3fvcr,
    section[data-testid="stSidebar"] .st-emotion-cache-1rs6os,
    section[data-testid="stSidebar"] .st-emotion-cache-17ziqus {
        display: none !important;
    }
    
    /* Alternative : masquer par attribut data-testid */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Masquer la navigation par défaut de Streamlit (nouvelle version) */
    .st-emotion-cache-1cypcdb, .st-emotion-cache-12fmjuu, .st-emotion-cache-1y4p8pa {
        display: none !important;
    }
    
    /* Masquer spécifiquement la sidebar de navigation des pages */
    div[data-testid="stSidebarNav"],
    section[data-testid="stSidebarNav"],
    .st-emotion-cache-1cypcdb,
    .st-emotion-cache-12fmjuu,
    [data-testid="stSidebarNavItems"],
    [data-testid="stSidebarNavLink"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }
    
    /* Force la navigation par défaut à disparaître */
    .css-pkbazv, .css-1v3fvcr, .e1fqkh3o0 {
        display: none !important;
    }
    </style>
    """

class GroqConfig:
    """Configuration pour l'assistant Groq."""
    
    MODEL_NAME = "llama-3.1-8b-instant"
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    
    SYSTEM_PROMPT = """
    Tu es un assistant IA spécialisé dans l'inspection de structures en béton et la détection de fissures.
    
    Ton rôle :
    - Aider les ingénieurs et techniciens du bâtiment
    - Expliquer les résultats d'analyse d'images
    - Donner des conseils techniques sur l'inspection
    - Guider dans l'utilisation de l'application
    
    Ton expertise couvre :
    - Analyse structurelle du béton
    - Interprétation des fissures
    - Normes de construction
    - Techniques d'inspection
    - Usage des outils IA
    
    Réponds de manière :
    - Professionnelle et technique
    - Claire et accessible
    - Avec des références aux normes si pertinent
    - En français
    
    Tu as accès aux résultats de l'analyse en cours et peux les commenter.
    """

class EmailConfig:
    """Configuration pour l'envoi d'emails."""
    
    # Configuration SMTP par défaut (Gmail)
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    USE_TLS = True
    
    # Templates d'email
    EMAIL_TEMPLATES = {
        'subject_single': "🔍 Rapport d'Analyse - Détection de Fissures",
        'subject_batch': "📊 Rapport d'Analyse Batch - Détection de Fissures",
        'subject_realtime': "📹 Rapport d'Analyse - Détection en temps réel de Fissures"
    }
    
    # Configuration des pièces jointes
    MAX_ATTACHMENT_SIZE_MB = 25  # Limite Gmail
    ALLOWED_ATTACHMENT_FORMATS = ['pdf', 'xlsx', 'png', 'jpg', 'jpeg']
    
    # Templates de contenu
    EMAIL_BODY_TEMPLATE = """
    Bonjour,
    
    Veuillez trouver ci-joint le rapport d'analyse de détection de fissures.
    
    📊 Résumé de l'analyse :
    {summary}
    
    📎 Fichiers joints :
    {attachments}
    
    Cette analyse a été générée automatiquement par l'application de Détection de Fissures.
    
    Cordialement,
    Système de Détection Automatique de Fissures
    """

class NotificationConfig:
    """Configuration pour les notifications."""
    
    # Types de notifications
    NOTIFICATION_TYPES = {
        'SUCCESS': {'icon': '✅', 'color': '#28a745'},
        'WARNING': {'icon': '⚠️', 'color': '#ffc107'},
        'ERROR': {'icon': '❌', 'color': '#dc3545'},
        'INFO': {'icon': 'ℹ️', 'color': '#17a2b8'}
    }

# Variables d'environnement par défaut
DEFAULT_ENV = {
    'GROQ_API_KEY': '',
    'DEBUG_MODE': 'False',
    'LOG_LEVEL': 'INFO',
    'SMTP_EMAIL': '',
    'SMTP_PASSWORD': '',
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': '587'
}