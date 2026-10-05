#!/usr/bin/env python3
"""
Assistant de Chat avec Groq
===========================

Module pour l'intégration du chat assistant IA
utilisant l'API Groq pour l'aide contextuelle.
"""

import streamlit as st
import os
from typing import List, Dict, Optional
import json
import time

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    # Ne pas appeler Streamlit au chargement du module

from config.config import GroqConfig

class ChatAssistant:
    """Assistant de chat pour l'application."""
    
    def __init__(self):
        self.client = None
        self.conversation_history = []
        self.max_history = 10
        self.initialize_client()
    
    def _get_groq_api_key(self) -> str:
        """Récupère la clé API Groq (override session > secrets > env)."""
        # Priorité à une clé saisie par l'utilisateur pendant la session
        api_key_override = st.session_state.get('GROQ_API_KEY_OVERRIDE')
        if api_key_override:
            return api_key_override
        try:
            # Secrets Streamlit
            key_from_secrets = st.secrets.get('GROQ_API_KEY')
        except Exception:
            key_from_secrets = None
        return key_from_secrets or os.getenv('GROQ_API_KEY') or ""
    
    def initialize_client(self):
        """Initialise le client Groq."""
        if not GROQ_AVAILABLE:
            return False
        
        api_key = self._get_groq_api_key()
        
        if not api_key:
            return False
        
        try:
            self.client = Groq(api_key=api_key)
            return True
        except Exception as e:
            # Ne pas écrire directement sur la page ici; gérer l'affichage dans le widget
            # Conserver une trace minimale en session pour le widget
            st.session_state["GROQ_INIT_ERROR"] = str(e)
            return False
    
    def is_available(self) -> bool:
        """Vérifie si le chat assistant est disponible."""
        return self.client is not None and GROQ_AVAILABLE
    
    def add_context(self, context_type: str, data: dict):
        """Ajoute du contexte à la conversation."""
        context_message = self._format_context(context_type, data)
        if context_message:
            self.conversation_history.append({
                "role": "system",
                "content": f"Contexte: {context_message}"
            })
    
    def _format_context(self, context_type: str, data: dict) -> str:
        """Formate le contexte selon le type."""
        if context_type == "analysis_result":
            predicted_class = data.get('predicted_class', 0)
            confidence = data.get('confidence', 0)
            metrics = data.get('metrics', {})
            
            result = "Fissure détectée" if predicted_class == 1 else "Aucune fissure"
            context = f"Résultat d'analyse: {result} (confiance: {confidence:.1%})"
            
            if metrics:
                context += f", Surface fissurée: {metrics.get('crack_percentage', 0):.2f}%"
                context += f", Nombre de fissures: {metrics.get('num_cracks', 0)}"
            
            return context
        
        elif context_type == "image_upload":
            filename = data.get('filename', 'image')
            size = data.get('size', 'inconnue')
            return f"Image uploadée: {filename} (taille: {size})"
        
        elif context_type == "page_visit":
            page = data.get('page', 'inconnue')
            return f"Utilisateur sur la page: {page}"
        
        return ""
    
    def chat(self, user_message: str, context: Optional[Dict] = None) -> str:
        """Envoie un message et retourne la réponse."""
        if not self.is_available():
            return (
                "Assistant indisponible. Configurez une clé Groq valide dans la section '🔑 Configurer la clé Groq' du panneau latéral."
            )
        
        try:
            # Ajouter le contexte si fourni
            if context:
                self.add_context(context.get('type', 'general'), context.get('data', {}))
            
            # Ajouter le message utilisateur
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Préparer les messages avec le système
            messages = [
                {"role": "system", "content": GroqConfig.SYSTEM_PROMPT}
            ] + self.conversation_history[-self.max_history:]
            
            # Appel à l'API Groq
            response = self.client.chat.completions.create(
                model=GroqConfig.MODEL_NAME,
                messages=messages,
                max_tokens=GroqConfig.MAX_TOKENS,
                temperature=GroqConfig.TEMPERATURE
            )
            
            assistant_response = response.choices[0].message.content
            
            # Ajouter la réponse à l'historique
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_response
            })
            
            # Limiter l'historique
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return assistant_response
            
        except Exception as e:
            error_text = str(e)
            # Détection d'erreur 401 / clé invalide
            if "invalid_api_key" in error_text.lower() or "401" in error_text:
                st.session_state["GROQ_INIT_ERROR"] = error_text
                return (
                    "Erreur lors de la communication avec l'assistant: Clé API invalide. "
                    "Vérifiez la clé Groq et réessayez."
                )
            return f"Erreur lors de la communication avec l'assistant: {error_text}"

    def chat_stream(self, user_message: str, context: Optional[Dict] = None):
        """Génère la réponse en flux (streaming) chunk par chunk.

        Rend des morceaux de texte successifs. À la fin, met à jour l'historique interne.
        """
        if not self.is_available():
            yield ""
            return

        try:
            # Ajouter le contexte si fourni
            if context:
                self.add_context(context.get('type', 'general'), context.get('data', {}))

            # Ajouter le message utilisateur à l'historique interne (pour le contexte)
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            messages = [
                {"role": "system", "content": GroqConfig.SYSTEM_PROMPT}
            ] + self.conversation_history[-self.max_history:]

            # Appel streaming
            stream = self.client.chat.completions.create(
                model=GroqConfig.MODEL_NAME,
                messages=messages,
                max_tokens=GroqConfig.MAX_TOKENS,
                temperature=GroqConfig.TEMPERATURE,
                stream=True,
            )

            full_text = ""
            for chunk in stream:
                try:
                    delta = chunk.choices[0].delta
                    piece = getattr(delta, 'content', None)
                except Exception:
                    piece = None
                if piece:
                    full_text += piece
                    yield piece

            # Mise à jour de l'historique complet
            if full_text:
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_text
                })

        except Exception as e:
            error_text = str(e)
            # Si streaming échoue, ne casse pas l'UI
            yield f"\n[Erreur: {error_text}]"
    
    def get_suggested_questions(self, page: str = "general") -> List[str]:
        """Retourne des questions suggérées selon la page."""
        suggestions = {
            "general": [
                "Comment utiliser cette application ?",
                "Quels sont les formats d'image supportés ?",
                "Comment interpréter les résultats ?",
                "Quelle est la précision des modèles ?"
            ],
            "detection": [
                "Comment améliorer la qualité de détection ?",
                "Que signifie le pourcentage de confiance ?",
                "Comment interpréter les métriques quantitatives ?",
                "Quand une fissure est-elle considérée comme critique ?"
            ],
            "batch": [
                "Combien d'images puis-je traiter en même temps ?",
                "Comment exporter les résultats ?",
                "Comment comparer plusieurs analyses ?",
                "Quels formats d'export sont disponibles ?"
            ],
            "realtime": [
                "Comment optimiser la détection en temps réel ?",
                "Quelle distance recommandez-vous ?",
                "Comment améliorer l'éclairage ?",
                "Puis-je sauvegarder les captures ?"
            ]
        }
        # Retirer la suggestion sur le choix de méthode DL/OpenCV
        for key in suggestions:
            suggestions[key] = [
                s for s in suggestions[key]
                if "Deep Learning" not in s and "OpenCV" not in s
            ]
        # Ajouter une suggestion utile à la place
        suggestions["detection"].append("Comment obtenir un bon masque de fissures avec OpenCV ?")
        
        return suggestions.get(page, suggestions["general"])
    
    def clear_history(self):
        """Efface l'historique de conversation."""
        self.conversation_history = []

@st.cache_resource
def get_chat_assistant():
    """Retourne une instance singleton du chat assistant."""
    return ChatAssistant()

def show_chat_widget(page: str = "general", context: Optional[Dict] = None):
    """Affiche le widget de chat."""
    assistant = get_chat_assistant()
    
    # Bloc de configuration de la clé API dans la sidebar
    with st.sidebar:
        st.markdown("---")
        with st.expander("🔑 Configurer la clé Groq", expanded=(not assistant.is_available())):
            current_key = st.session_state.get('GROQ_API_KEY_OVERRIDE', "")
            api_key_input = st.text_input(
                "GROQ_API_KEY",
                value=current_key,
                type="password",
                help="Collez ici votre clé Groq pour activer l'assistant",
            )
            colk1, colk2 = st.columns(2)
            with colk1:
                if st.button("Enregistrer la clé"):
                    st.session_state['GROQ_API_KEY_OVERRIDE'] = api_key_input.strip()
                    # Ré-initialiser le client
                    assistant.initialize_client()
                    # Pas de rerun automatique
            with colk2:
                if st.button("Effacer la clé"):
                    st.session_state.pop('GROQ_API_KEY_OVERRIDE', None)
                    assistant.initialize_client()
                    # Pas de rerun automatique

            init_err = st.session_state.get("GROQ_INIT_ERROR")
            if init_err:
                if "invalid api key" in init_err.lower() or "401" in init_err:
                    st.error("Clé API invalide (401). Veuillez saisir une clé valide.")
                else:
                    st.warning(f"Info: {init_err}")
    
    if not assistant.is_available():
        with st.sidebar:
            st.warning("💬 Chat Assistant indisponible sans clé valide.")
        return
    
    # Widget de chat dans la sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 💬 Assistant IA")
        
        # Initialiser l'état du chat
        if 'selected_suggestion' not in st.session_state:
            st.session_state['selected_suggestion'] = ""
        
        # Questions suggérées
        with st.expander("💡 Questions Suggérées", expanded=False):
            suggestions = assistant.get_suggested_questions(page)
            for i, suggestion in enumerate(suggestions):
                if st.button(suggestion, key=f"suggestion_{i}"):
                    st.session_state['selected_suggestion'] = suggestion
        
        # Zone de chat - utiliser la suggestion sélectionnée comme valeur par défaut
        default_value = st.session_state.get('selected_suggestion', "")
        user_message = st.text_input(
            "Posez votre question:",
            value=default_value,
            key="chat_input",
            placeholder="Ex: Comment interpréter ces résultats ?"
        )
        
        # Réinitialiser la suggestion après utilisation
        if st.session_state.get('selected_suggestion') and user_message == default_value:
            st.session_state['selected_suggestion'] = ""
        
        if st.button("Envoyer", type="primary") and user_message:
            with st.spinner("Assistant en réflexion..."):
                response = assistant.chat(user_message, context)
            
            # Afficher la conversation
            st.markdown("**Vous:**")
            st.write(user_message)
            st.markdown("**Assistant:**")
            st.write(response)
            
            # Pas de rerun automatique; on nettoie seulement la suggestion
            st.session_state['selected_suggestion'] = ""
        
        # Bouton pour effacer l'historique
        if st.button("🗑️ Effacer l'historique"):
            assistant.clear_history()
            st.success("Historique effacé!")

def show_floating_chat():
    """Affiche un chat flottant (expérimental)."""
    assistant = get_chat_assistant()
    
    if not assistant.is_available():
        return
    
    # CSS pour le chat flottant
    st.markdown("""
    <style>
    .floating-chat {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: #2c5282;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .floating-chat:hover {
        background: #ff6b35;
        transform: scale(1.1);
    }
    
    .floating-chat-icon {
        color: white;
        font-size: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Widget flottant
    st.markdown("""
    <div class="floating-chat" onclick="document.getElementById('chat-modal').style.display='block'">
        <div class="floating-chat-icon">💬</div>
    </div>
    """, unsafe_allow_html=True)

def get_context_for_analysis(result: Dict) -> Dict:
    """Crée un contexte pour l'assistant basé sur les résultats d'analyse."""
    return {
        'type': 'analysis_result',
        'data': {
            'predicted_class': result.get('predicted_class'),
            'confidence': result.get('confidence'),
            'metrics': result.get('metrics', {})
        }
    }

def get_context_for_page(page_name: str) -> Dict:
    """Crée un contexte pour l'assistant basé sur la page courante."""
    return {
        'type': 'page_visit',
        'data': {'page': page_name}
    }