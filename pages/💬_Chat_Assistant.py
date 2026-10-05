#!/usr/bin/env python3
"""
Page Chat Assistant - Assistant IA avec Groq
===========================================

Cette page offre un assistant conversationnel intelligent pour 
guider les utilisateurs dans l'utilisation de l'application.
"""

import streamlit as st
import os
from pathlib import Path
import sys

# Ajouter le répertoire parent au path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

# Imports des modules de l'application
from utils.chat_assistant import ChatAssistant, show_chat_widget
from utils.sidebar import show_unified_sidebar, show_footer

def setup_page():
    """Configure la page."""
st.set_page_config(
    page_title="💬 Chat Assistant",
    page_icon="💬",
    layout="wide"
)

    # Affichage de la sidebar unifiée
show_unified_sidebar("Chat Assistant")

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


def setup_content():
    """Configure l'en-tête et le contenu."""
    st.markdown("# 💬 Chat Assistant")
    st.markdown("### Assistant IA pour vous guider dans l'application")
    
    # Style CSS personnalisé pour le chat (thème noir cohérent)
    st.markdown("""
    <style>
    .chat-container {
        background: #111111;
        border: 1px solid #333333;
        padding: 1.5rem;
        border-radius: 8px;
        color: white;
        margin: 1rem 0;
    }
    .user-message {
        background: linear-gradient(135deg, #8B0000, #A52A2A);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    .assistant-message {
        background: linear-gradient(135deg, #4CAF50, #2E7D32);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
    }
    /* Animation de saisie en cours */
    .typing-bubble {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        display: inline-block;
    }
    .typing { display: inline-block; }
    .typing .dot {
        height: 8px; width: 8px; margin: 0 2px; background: #fff; border-radius: 50%;
        display: inline-block; animation: blink 1.4s infinite both;
    }
    .typing .dot:nth-child(2) { animation-delay: .2s; }
    .typing .dot:nth-child(3) { animation-delay: .4s; }
    @keyframes blink { 0% { opacity: .2 } 20% { opacity: 1 } 100% { opacity: .2 } }
    .suggestion-button {
        background: #333333;
        border: 1px solid #555555;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .suggestion-button:hover {
        background: #555555;
        border-color: #777777;
    }
    </style>
    """, unsafe_allow_html=True)


def check_groq_availability():
    """Vérifie si l'API Groq est disponible."""
    try:
        groq_key = os.getenv("GROQ_API_KEY")
        return groq_key is not None and groq_key.strip() != ""
    except Exception:
        return False

def get_fallback_response(question: str) -> str:
    """Fournit des réponses de base si Groq n'est pas disponible."""
    question_lower = question.lower()
    
    if "interpréter" in question_lower or "résultat" in question_lower:
        return """
        🎯 **Interprétation des résultats de détection :**
        
        • **Vert** ✅ : Aucune fissure détectée (confiance > 80%)
        • **Rouge** ⚠️ : Fissure détectée (confiance > 70%)
        • **Orange** 🟡 : Incertitude (confiance < 70%)
        
        **Métriques importantes :**
        - **Confiance** : Probabilité de la prédiction (0-100%)
        - **Surface fissurée** : Zone affectée en pixels/mm²
        - **Sévérité** : Niveau de risque estimé
        
        Consultez les visualisations pour localiser précisément les fissures détectées.
        """
    
    elif "méthode" in question_lower or "choisir" in question_lower:
        return """
        🤖 **Choix de méthode d'analyse :**
        
        **Deep Learning (Recommandé) :**
        • Plus précis sur des structures complexes
        • Détection fine des micro-fissures
        • Robuste aux variations d'éclairage
        • Temps : 2-3 secondes par image
        
        **OpenCV (Classique) :**
        • Plus rapide (< 1 seconde)
        • Bon pour fissures évidentes
        • Moins de ressources requises
        • Paramètres ajustables manuellement
        
        💡 **Conseil :** Utilisez le mode hybride pour combiner les deux approches !
        """
    
    else:
        return """
        💬 **Assistant de détection de fissures disponible !**
        
        Je peux vous aider avec :
        • Interprétation des résultats d'analyse
        • Choix de la méthode de détection appropriée
        • Optimisation des paramètres
        • Conseils pour de meilleures captures d'images
        • Explication des métriques de performance
        
        Posez-moi une question spécifique sur la détection de fissures !
        """

def show_welcome_message():
    """Affiche le message de bienvenue."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    ">
        <h2 style="margin: 0 0 1rem 0;">🤖 Assistant IA Spécialisé</h2>
        <p style="margin: 0; opacity: 0.9;">
            Votre expert en détection de fissures est prêt à vous aider !
            Posez vos questions ou choisissez un sujet ci-dessous.
        </p>
    </div>
    """, unsafe_allow_html=True)

def initialize_chat():
    """Initialise les variables de session pour le chat."""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'assistant_ready' not in st.session_state:
        st.session_state.assistant_ready = check_groq_availability()

def show_chat_interface():
    """Affiche l'interface de chat avec l'assistant."""
    st.markdown("### 💬 Conversation")
    
    # Zone réactive pour l'historique (mise à jour sans rerun)
    render_area = st.empty()

    def render_history():
        with render_area.container():
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                            # Message utilisateur aligné à droite
                    st.markdown(f"""
                                <div style="display: flex; justify-content: flex-end; margin: 1rem 0;">
                                    <div style="
                                        background: linear-gradient(135deg, #8B0000, #A52A2A);
                                        color: white;
                                        padding: 0.8rem 1.2rem;
                                        border-radius: 18px 18px 4px 18px;
                                        max-width: 70%;
                                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                        font-size: 0.95rem;
                                        line-height: 1.4;
                                    ">
                                        {message["content"]}
                                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                            # Message assistant aligné à gauche
                    st.markdown(f"""
                                <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                                    <div style="
                                        display: flex; 
                                        align-items: flex-start;
                                        max-width: 80%;
                                    ">
                                        <div style="
                                            background: linear-gradient(135deg, #0f172a, #1e293b);
                                            color: white;
                                            width: 32px; height: 32px;
                                            border-radius: 50%;
                                            display: flex;
                                            align-items: center;
                                            justify-content: center;
                                            margin-right: 0.8rem;
                                            font-size: 1.2rem;
                                            flex-shrink: 0;
                                        ">🤖</div>
                                        <div style="
                                            background: linear-gradient(135deg, #0f172a, #1e293b);
                                            color: white;
                                            padding: 0.8rem 1.2rem;
                                            border-radius: 18px 18px 18px 4px;
                                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                            font-size: 0.95rem;
                                            line-height: 1.4;
                                        ">
                                            {message["content"].replace(chr(10), '<br>')}
                                        </div>
                                    </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Rendu initial
    render_history()
    
    # Interface de saisie avec chat_input pour support d'Entrée
    user_input = st.chat_input("Posez votre question sur la détection de fissures...")
    
    if user_input:
        # Ajouter le message utilisateur à l'historique immédiatement
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Obtenir la réponse de l'assistant (streaming si possible)
        if st.session_state.assistant_ready:
            try:
                assistant = ChatAssistant()
                # Zone de rendu en temps réel
                with st.spinner("Assistant en saisie..."):
                    placeholder = st.empty()
                    # Afficher une bulle "saisie en cours"
                    placeholder.markdown("""
                        <div style="display: flex; justify-content: flex-start; margin: 1rem 0;">
                            <div class="typing-bubble">
                                <div class="typing">
                                    <span class="dot"></span>
                                    <span class="dot"></span>
                                    <span class="dot"></span>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    streamed_text = ""
                    for piece in assistant.chat_stream(user_input, get_context_for_page("chat")):
                        if piece:
                            streamed_text += piece
                            placeholder.markdown(f"""
                                <div class="assistant-message">
                                    <strong>🤖 Assistant :</strong> {streamed_text}
                                </div>
                            """, unsafe_allow_html=True)
                    # Préparer la réponse finale
                    response = streamed_text.strip() if streamed_text.strip() else get_fallback_response(user_input)
            except Exception as e:
                response = f"Erreur de l'assistant : {e}"
        else:
            # Mode limité (pas de streaming)
            response = get_fallback_response(user_input)
        
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Limiter l'historique
        if len(st.session_state.chat_history) > 20:
            st.session_state.chat_history = st.session_state.chat_history[-20:]
        
        # Rafraîchir l'affichage immédiatement
        render_history()
    
    # Boutons de suggestion si pas d'historique
    if not st.session_state.chat_history:
        st.markdown("### 💡 Questions Suggérées")
        col1 = st.columns(1)[0]
        with col1:
            if st.button("Comment interpréter un résultat de détection ?", key="suggestion_1"):
                handle_suggested_question("Comment interpréter un résultat de détection ?")
    
    # Bouton pour effacer l'historique
    if st.session_state.chat_history:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_history = []

    # Si une question suggérée a été traitée, rafraîchir l'affichage
    if st.session_state.get("force_refresh_chat"):
        render_history()
        st.session_state["force_refresh_chat"] = False

def handle_suggested_question(question: str):
    """Gère une question suggérée en ajoutant la question et la réponse à l'historique."""
    # Ajouter la question utilisateur
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Afficher un message temporaire pendant la génération
    with st.spinner("L'assistant génère une réponse..."):
        # Générer la réponse de l'assistant
        if st.session_state.assistant_ready:
            try:
                assistant = ChatAssistant()
                response = assistant.chat(question, get_context_for_page("chat"))
            except Exception as e:
                response = f"Erreur de l'assistant : {e}"
        else:
            response = get_fallback_response(question)
    
    # Ajouter la réponse à l'historique
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response
    })
    # Forcer le rafraîchissement du rendu sans rerun global
    st.session_state["force_refresh_chat"] = True

def show_help_section():
    """Affiche la section d'aide."""
    st.markdown("### ❓ Aide & Fonctionnalités")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🔍 Détection Simple"):
            st.markdown("""
            **Fonctionnalités :**
            - Upload d'une seule image
            - Analyse complète automatique
            - Visualisations détaillées
            - Métriques de confiance
            """)
        
        with st.expander("📊 Analyse Batch"):
            st.markdown("""
            **Utilisation :**
            - Uploadez plusieurs images simultanément
            - Traitement automatique de toutes les images
            - Export des résultats en CSV/Excel
            - Statistiques globales générées
            """)
    
    with col2:
        with st.expander("📹 Temps Réel"):
            st.markdown("""
            **Fonctionnalités :**
            - Détection via webcam en direct
            - Analyse frame par frame
            - Capture d'images d'intérêt
            - Simulation temps réel sur images uploadées
            """)
        
        with st.expander("📈 Tableau de Bord"):
            st.markdown("""
            **Statistiques :**
            - Historique des analyses
            - Graphiques de performance
            - Tendances temporelles
            - Export des rapports
            """)

def get_context_for_page(page_name):
    """Fournit le contexte pour une page spécifique."""
    return {
        "page": page_name,
        "application": "Détection de Fissures",
        "models": ["Classification ResNet50", "Segmentation UNet"],
        "features": ["Détection Simple", "Analyse Batch", "Temps Réel", "Chat Assistant"]
    }

def main():
    """Fonction principale de la page."""
    setup_page()
    initialize_chat()
    
    # Informations sur l'état de l'assistant
    if st.session_state.assistant_ready:
        st.success("✅ Assistant IA connecté")
    else:
        st.warning("⚠️ Assistant en mode limité (Groq API non configurée)")
    
    st.markdown("""
        Cette page vous donne accès à un assistant IA spécialisé dans la détection de fissures.
        
        **💡 L'assistant peut vous aider avec :**
        - Interprétation des résultats de détection
        - Choix de la méthode d'analyse appropriée  
        - Optimisation des paramètres
        - Conseils pour améliorer vos images
        - Questions techniques sur l'application
        """)
    
    # Message de bienvenue si pas d'historique
    if not st.session_state.chat_history:
        show_welcome_message()
    
    # Interface de chat principale
    show_chat_interface()
    
    st.markdown("---")
    
    # Section d'aide
    show_help_section()
    
    # Footer
    st.markdown("""
    ---
    💡 **Conseil :** L'assistant est formé pour vous aider spécifiquement avec la détection de fissures. 
    N'hésitez pas à poser des questions techniques détaillées !
    """)
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()