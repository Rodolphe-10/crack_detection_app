#!/usr/bin/env python3
"""
Page de Détection Simple - Version Améliorée
===========================================

Interface pour l'analyse d'une seule image avec
classification et segmentation hybride (Deep Learning + OpenCV).
"""

import streamlit as st
import torch
import torch.nn.functional as F
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import time
from pathlib import Path
import sys

# Ajouter le répertoire parent au path pour les imports
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from config.config import AppConfig, StreamlitConfig
from utils.model_loader import load_models, setup_device
from utils.image_processor import (
    preprocess_image_for_classification, 
    run_classification_analysis, 
    run_segmentation_analysis,
    run_opencv_segmentation,
    safe_model_inference,
    validate_image_for_analysis,
    get_validation_details
)
from utils.validation_simple import validate_image_for_analysis_simple
from utils.email_sender import EmailInterface
from utils.reporting import create_simple_report_pdf
from utils.history_store import log_analysis
from utils.sidebar import show_unified_sidebar, show_footer
from utils.chat_assistant import ChatAssistant, get_chat_assistant

def setup_page():
    """Configure la page et l'en-tête."""
    # Affichage de la sidebar unifiée
    show_unified_sidebar("Détection Simple")
    
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


    
    st.markdown("# 🔍 Détection Simple")
    st.markdown("### Analyse avancée d'une image (OpenCV)")
    
    # CSS personnalisé pour cette page
    st.markdown("""
    <style>
    .analysis-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    .result-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        color: black;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .warning-card {
        background: #fff8f8;
    }
    .method-selector {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    /* Styles pour le chat conversationnel (même que Chat Assistant) */
    .chat-section {
        background: #111111;
        border: 1px solid #333333;
        padding: 1.5rem;
        border-radius: 8px;
        color: white;
        margin: 1.5rem 0;
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

def show_introduction():
    """Affiche l'introduction de la page."""
    st.markdown("""
    <div class="analysis-container">
        <h3>🎯 Analyse Intelligente d'Images</h3>
        <p>Cette page utilise un système hybride combinant :</p>
        <ul>
            <li><strong>🔧 OpenCV</strong> : Traitement d'image rapide et efficace</li>
        </ul>
        <p><strong>📊 Résultats :</strong> Détection + Segmentation binaire des fissures</p>
    </div>
    """, unsafe_allow_html=True)

def show_analysis_chat(analysis_results: dict):
    """Affiche le chat conversationnel pour interpréter les résultats d'analyse."""
    st.markdown("### 💬 Assistant IA - Interprétation des Résultats")
    
    # Initialiser l'assistant
    assistant = get_chat_assistant()
    
    if not assistant.is_available():
        st.info("💡 Pour activer l'assistant IA, configurez votre clé Groq dans la sidebar.")
        return
    
    # Ajouter le contexte des résultats d'analyse
    context = {
        'type': 'analysis_result',
        'data': {
            'predicted_class': analysis_results.get('pred_class', 0),
            'confidence': analysis_results.get('conf', 0),
            'analysis_time': analysis_results.get('analysis_time', 0),
            'has_mask': analysis_results.get('mask') is not None
        }
    }
    
    # Initialiser l'historique de chat pour cette session (même système que Chat Assistant)
    if 'detection_chat_history' not in st.session_state:
        st.session_state.detection_chat_history = []
        # Message de bienvenue contextuel
        welcome_msg = f"Bonjour ! Je vois que vous avez analysé une image. "
        if context['data']['predicted_class'] == 1:
            welcome_msg += f"Une fissure a été détectée avec {context['data']['confidence']:.1%} de confiance. "
            if context['data']['has_mask']:
                welcome_msg += "La segmentation a également été effectuée. "
        else:
            welcome_msg += f"Aucune fissure détectée ({context['data']['confidence']:.1%} de confiance). "
        welcome_msg += "Comment puis-je vous aider à interpréter ces résultats ?"
        
        st.session_state.detection_chat_history.append({
            "role": "assistant",
            "content": welcome_msg
        })
    
    # Zone réactive pour l'historique (même système que Chat Assistant)
    render_area = st.empty()

    def render_history():
        with render_area.container():
            for message in st.session_state.detection_chat_history:
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
    
    # Si un rafraîchissement forcé est demandé, le faire
    if st.session_state.get("force_refresh_detection_chat"):
        render_history()
        st.session_state["force_refresh_detection_chat"] = False
    
    # Questions suggérées (même système que Chat Assistant)
    if not st.session_state.detection_chat_history or len(st.session_state.detection_chat_history) <= 1:
        st.markdown("### 💡 Questions Suggérées")
        suggestions = [
            "Comment interpréter ce niveau de confiance ?",
            "Que signifie ce résultat pour la sécurité ?",
            "Comment améliorer la qualité de détection ?",
            "Quelles sont les prochaines étapes recommandées ?"
        ]
        
        col1 = st.columns(1)[0]
        with col1:
            for i, suggestion in enumerate(suggestions):
                if st.button(suggestion, key=f"detection_suggestion_{i}"):
                    handle_suggested_question(suggestion, context, assistant)
                    # Rafraîchir immédiatement après le clic
                    render_history()
    
    # Interface de saisie avec chat_input (même que Chat Assistant)
    user_input = st.chat_input("Posez votre question sur les résultats d'analyse...")
    
    if user_input:
        # Ajouter le message utilisateur à l'historique immédiatement
        st.session_state.detection_chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Obtenir la réponse de l'assistant (streaming si possible)
        try:
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
                for piece in assistant.chat_stream(user_input, context):
                    if piece:
                        streamed_text += piece
                        placeholder.markdown(f"""
                            <div class="assistant-message">
                                <strong>🤖 Assistant :</strong> {streamed_text}
                            </div>
                        """, unsafe_allow_html=True)
                # Préparer la réponse finale
                response = streamed_text.strip() if streamed_text.strip() else "Désolé, je n'ai pas pu générer une réponse."
        except Exception as e:
            response = f"Erreur de l'assistant : {e}"
        
        st.session_state.detection_chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        # Limiter l'historique
        if len(st.session_state.detection_chat_history) > 20:
            st.session_state.detection_chat_history = st.session_state.detection_chat_history[-20:]
        
        # Rafraîchir l'affichage immédiatement
        render_history()
    
    # Bouton pour effacer l'historique (même système que Chat Assistant)
    if st.session_state.detection_chat_history and len(st.session_state.detection_chat_history) > 1:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.detection_chat_history = []
            # Rafraîchir immédiatement après le clic
            render_history()

def handle_suggested_question(question: str, context: dict, assistant):
    """Gère une question suggérée en ajoutant la question et la réponse à l'historique."""
    # Ajouter la question utilisateur
    st.session_state.detection_chat_history.append({
        "role": "user",
        "content": question
    })
    
    # Afficher un message temporaire pendant la génération
    with st.spinner("L'assistant génère une réponse..."):
        # Générer la réponse de l'assistant
        try:
            response = assistant.chat(question, context)
        except Exception as e:
            response = f"Erreur de l'assistant : {e}"
    
    # Ajouter la réponse à l'historique
    st.session_state.detection_chat_history.append({
        "role": "assistant",
        "content": response
    })
    # Le rafraîchissement sera fait directement dans le bouton

def show_download_buttons(analysis_summary, image, mask, pred_class, conf, analysis_time):
    """Affiche les boutons de téléchargement de manière stable."""
    st.markdown("### 📤 Export & Partage")
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Préparer des figures pour enrichir le PDF
        figures = {}
        try:
            figures["original"] = image
            if mask is not None:
                figures["mask"] = (mask / 255.0) if mask.dtype == np.uint8 else (mask > 0).astype(np.float32) * 255.0
                # Overlay reconstitué
                overlay = image.copy()
                if len(overlay.shape) == 2:
                    overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
                crack_mask = (mask > 0.1)
                overlay[crack_mask] = [255, 0, 0]
                alpha = 0.6
                figures["overlay"] = cv2.addWeighted(image, 1-alpha, overlay, alpha, 0)
        except Exception:
            pass
        enriched = {**analysis_summary, "figures": figures}
        pdf_bytes = create_simple_report_pdf(enriched)
        st.download_button(
            label="📄 Télécharger PDF",
            data=pdf_bytes,
            file_name=f"rapport_detection_{int(time.time())}.pdf",
            mime="application/pdf",
            key="download_pdf_simple"
        )
    
    with col_b:
        import pandas as pd
        df = pd.DataFrame([
            {
                'Resultat': AppConfig.CLASSIFICATION_CLASSES[pred_class],
                'Confiance': f"{conf:.1%}",
                'Temps_s': f"{analysis_time:.2f}",
            }
        ])
        st.download_button(
            label="🧾 Télécharger CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name=f"resultat_detection_{int(time.time())}.csv",
            mime="text/csv",
            key="download_csv_simple"
        )

    st.markdown("### ✉️ Partage par Email")
    EmailInterface().show_send_email_interface(
        analysis_results=analysis_summary,
        attachments=None
    )

def main():
    """Fonction principale de la page."""
    setup_page()
    show_introduction()
    
    # Upload d'image
    st.markdown("### 📤 Sélection d'Image")
    uploaded_file = st.file_uploader(
        "Choisissez une image à analyser",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        help="Formats supportés : JPG, PNG, BMP, TIFF (max 200MB)",
        key="simple_uploader"
    )
    # Si une nouvelle image est chargée, réinitialiser l'état sans rerun
    if uploaded_file is not None:
        current_upload_key = f"{uploaded_file.name}-{getattr(uploaded_file, 'size', 0)}"
        if st.session_state.get("simple_last_upload_key") != current_upload_key:
            st.session_state["simple_last_upload_key"] = current_upload_key
            # Nettoyer les résultats et le chat précédents pour repartir de zéro
            st.session_state.pop("simple_result", None)
            st.session_state.pop("detection_chat_history", None)
            st.session_state.pop("force_refresh_detection_chat", None)
            # Pas de rerun - l'interface se mettra à jour naturellement
    
    # Suppression de l'encart "Dernier Résultat - Export & Partage"
    
    if uploaded_file is not None:
        # Charger et afficher l'image
        image = Image.open(uploaded_file)
        image = np.array(image)
        
        # Convertir RGBA en RGB si nécessaire
        if len(image.shape) == 3 and image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        elif len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        st.markdown("### 🖼️ Image Sélectionnée")
        st.image(image, caption=f"Image chargée: {uploaded_file.name}", use_container_width=True)
        
        # Validation de l'image pour l'analyse de fissures
        st.markdown("### 🔍 Validation de l'Image")
        
        # Option pour désactiver la validation stricte
        col1, col2 = st.columns([3, 1])
        with col1:
            strict_validation = st.checkbox(
                "🔒 Validation stricte du béton", 
                value=True, 
                help="Décochez cette option si votre image valide est rejetée"
            )
        with col2:
            if not strict_validation:
                st.info("⚠️ Mode flexible activé")
                st.info("💡 L'image sera acceptée même si elle échoue la validation stricte du béton")
        
        with st.spinner("🔍 Validation de l'image..."):
            # Pour Détection Simple: validation dédiée plus permissive
            is_valid, validation_msg = validate_image_for_analysis_simple(image)
            
            if is_valid:
                st.success(validation_msg)
                
                # Afficher les détails de validation
                with st.expander("📊 Détails de validation"):
                    details = get_validation_details(image)
                    if "error" not in details:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Forme", f"{details['image_shape']}")
                            st.metric("Pixels", f"{details['size_pixels']:,}")
                            st.metric("Entropie", f"{details['entropy']:.2f}")
                        with col2:
                            st.metric("Variance locale", f"{details['local_variance']:.1f}")
                            st.metric("Densité contours", f"{details['edge_density']:.3f}")
                            if 'avg_saturation' in details:
                                st.metric("Saturation", f"{details['avg_saturation']:.1f}")
                
                # Bouton d'analyse avec cache pour éviter les rechargements
                analyze_clicked = st.button("🚀 Lancer l'Analyse Complète", type="primary", use_container_width=True, key="analyze_btn_main")
                
            else:
                st.error(validation_msg)
                st.warning("""
                **💡 Conseils pour une image valide :**
                - Utilisez une image de **mur en béton**, **sol en béton** ou **structure en béton**
                - Évitez les images de **forêt**, **paysage**, **portrait** ou **autres surfaces**
                - Assurez-vous que l'image est **claire** et **bien éclairée**
                - L'image doit montrer une **surface plane** en béton
                """)
                
                # Afficher les détails de validation même en cas d'échec
                with st.expander("📊 Détails de validation"):
                    details = get_validation_details(image)
                    if "error" not in details:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Forme", f"{details['image_shape']}")
                            st.metric("Pixels", f"{details['size_pixels']:,}")
                            st.metric("Entropie", f"{details['entropy']:.2f}")
                        with col2:
                            st.metric("Variance locale", f"{details['local_variance']:.1f}")
                            st.metric("Densité contours", f"{details['edge_density']:.3f}")
                            if 'avg_saturation' in details:
                                st.metric("Saturation", f"{details['avg_saturation']:.1f}")
                
                # Désactiver le bouton d'analyse si l'image n'est pas valide
                analyze_clicked = False
        
        if analyze_clicked:
            # Utiliser un cache pour éviter les rechargements répétés
            if "analysis_in_progress" not in st.session_state:
                st.session_state.analysis_in_progress = True

            start_time = time.time()
            
            try:
                # Chargement des modèles avec cache
                @st.cache_resource
                def get_models():
                    return load_models(), setup_device()

                with st.spinner("🔄 Chargement des modèles IA..."):
                    (classification_model, segmentation_model), device = get_models()
                
                if classification_model is None:
                    st.error("❌ Modèle de classification non disponible")
                    return
                
                # === CLASSIFICATION ===
                st.markdown("### 🎯 Étape 1 : Classification")
                with st.spinner("🧠 Analyse par Intelligence Artificielle..."):
                    result = run_classification_analysis(classification_model, image)
                    if result is None:
                        st.error("❌ Échec de l'analyse de classification")
                        return

                    pred_class, conf, probs_np = result
                    
                    # Vérification supplémentaire des valeurs
                    if pred_class is None or conf is None:
                        st.error("❌ Résultats de classification invalides")
                        return

                # Affichage des résultats de classification
                class_name = AppConfig.CLASSIFICATION_CLASSES[pred_class]
                
                if pred_class == 1:  # Fissure détectée
                    st.error(f"⚠️ **{class_name}** détectée avec {conf:.1%} de confiance")
                else:  # Pas de fissure
                    st.success(f"✅ **{class_name}** - {conf:.1%} de confiance")
                
                # Métriques détaillées
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Prédiction", class_name)
                with col2:
                    st.metric("Confiance", f"{conf:.1%}")
                with col3:
                    if pred_class == 1:
                        st.metric("Statut", "⚠️ Fissure", delta="Inspection requise")
                    else:
                        st.metric("Statut", "✅ Sain", delta="Aucune action")
                
                # === SEGMENTATION si fissure détectée (OpenCV uniquement) ===
                mask = None
                if pred_class == 1:
                    st.markdown("### 🎯 Étape 2 : Localisation des Fissures (OpenCV)")
                    with st.spinner("🔧 Segmentation OpenCV en cours..."):
                        mask = run_opencv_segmentation(image)
                        if mask is None or mask.size == 0:
                            st.warning("❌ Échec de la segmentation OpenCV")
                        else:
                            st.markdown("#### 📊 Résultats de Segmentation OpenCV")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.image(image, caption="Image originale", use_container_width=True)
                            with col2:
                                # Affichage type evaluate_model: 2D float 0..1 en niveaux de gris
                                mask_display = (
                                    (mask.astype(np.float32) / 255.0)
                                    if mask.dtype == np.uint8
                                    else (mask > 0).astype(np.float32)
                                )
                                st.image(mask_display, caption="Prédiction (Binaire)", use_container_width=True, clamp=True)
                            with col3:
                                # Overlay avec fissures en rouge
                                overlay = image.copy()
                                if len(overlay.shape) == 2:
                                    overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2RGB)
                                crack_mask = (mask > 0.1).astype(bool)
                                overlay[crack_mask] = [255, 0, 0]
                                alpha = 0.6
                                result = cv2.addWeighted(image, 1-alpha, overlay, alpha, 0)
                                st.image(result, caption="Overlay", use_container_width=True)
                
                # === RÉSUMÉ ===
                end_time = time.time()
                analysis_time = end_time - start_time

                # === JOURNALISATION DANS L'HISTORIQUE ===
                try:
                    log_analysis(
                        page="simple",
                        method="upload",
                        has_crack=bool(pred_class == 1),
                        confidence=float(conf),
                        analysis_time=float(analysis_time),
                        filename=uploaded_file.name if uploaded_file else None,
                        extra={
                            "pred_class": int(pred_class) if pred_class is not None else -1,
                            "has_mask": mask is not None,
                            "mask_area": float(np.sum(mask > 0) / mask.size * 100) if mask is not None else None,
                        }
                    )
                except Exception as e:
                    st.warning(f"⚠️ Impossible d'enregistrer dans l'historique: {e}")

                st.markdown("### 📋 Résumé de l'Analyse")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Résultat", AppConfig.CLASSIFICATION_CLASSES[pred_class])
                with col2:
                    st.metric("Confiance", f"{conf:.1%}")
                with col3:
                    st.metric("Temps d'analyse", f"{analysis_time:.2f}s")

                # === CHAT CONVERSATIONNEL ===
                show_analysis_chat({
                    "pred_class": int(pred_class) if pred_class is not None else -1,
                    "conf": float(conf),
                    "analysis_time": float(analysis_time),
                    "mask": mask,
                })

                # === EXPORT & EMAIL ===
                # Construire un petit dict résultat pour le PDF/email
                analysis_summary = {
                    'type': 'Simple',
                    'classification': {
                        'has_crack': bool(pred_class == 1),
                        'confidence': float(conf)
                    }
                }
                
                # Sauvegarder les résultats pour les téléchargements persistants
                st.session_state["simple_result"] = {
                    "pred_class": int(pred_class) if pred_class is not None else -1,
                    "conf": float(conf),
                    "analysis_time": float(analysis_time),
                    "mask": mask,
                    "image": image,
                    "analysis_summary": analysis_summary
                }
                
                # Afficher les boutons de téléchargement de manière stable
                show_download_buttons(analysis_summary, image, mask, pred_class, conf, analysis_time)
                
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse : {e}")
            finally:
                st.session_state.analysis_in_progress = False
    
        # Afficher les résultats persistés si l'utilisateur interagit avec d'autres boutons (download/email)
        if not analyze_clicked and "simple_result" in st.session_state:
            sr = st.session_state["simple_result"]
            st.markdown("### 🎯 Résultats (persistants)")
            class_name = AppConfig.CLASSIFICATION_CLASSES[1] if sr["pred_class"] == 1 else AppConfig.CLASSIFICATION_CLASSES[0]
            if sr["pred_class"] == 1:
                st.error(f"⚠️ {class_name} détectée avec {sr['conf']:.1%} de confiance")
            else:
                st.success(f"✅ {class_name} - {sr['conf']:.1%} de confiance")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prédiction", class_name)
            with col2:
                st.metric("Confiance", f"{sr['conf']:.1%}")
            with col3:
                st.metric("Temps d'analyse", f"{sr['analysis_time']:.2f}s")

            if sr["pred_class"] == 1 and sr.get("mask") is not None:
                st.markdown("#### 📊 Résultats de Segmentation OpenCV")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.image(sr["image"], caption="Image originale", use_container_width=True)
                with col2:
                    m = sr["mask"]
                    if m.dtype == np.uint8:
                        mask_display = (m / 255.0).astype(np.float32)
                    else:
                        mask_display = (m > 0).astype(np.float32)
                    st.image(mask_display, caption="Prédiction (Binaire)", use_container_width=True, clamp=True)
                with col3:
                    overlay = sr["image"].copy()
                    if len(overlay.shape) == 2:
                        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2RGB)
                    crack_mask = (sr["mask"] > 0.1).astype(bool)
                    overlay[crack_mask] = [255, 0, 0]
                    alpha = 0.6
                    result_img = cv2.addWeighted(sr["image"], 1-alpha, overlay, alpha, 0)
                    st.image(result_img, caption="Overlay", use_container_width=True)

            # === CHAT CONVERSATIONNEL ===
            show_analysis_chat({
                "pred_class": sr["pred_class"],
                "conf": sr["conf"],
                "analysis_time": sr["analysis_time"],
                "mask": sr.get("mask"),
            })

            # Export & Email re-rendus sans relancer l'analyse
            show_download_buttons(
                sr["analysis_summary"], 
                sr.get("image"), 
                sr.get("mask"), 
                sr["pred_class"], 
                sr["conf"], 
                sr["analysis_time"]
            )
    
    else:
        # Instructions d'utilisation
        st.markdown("""
        ### 💡 Instructions d'Utilisation
        
        1. **📤 Uploadez votre image** en utilisant le sélecteur ci-dessus
        2. **🔍 Formats supportés** : JPG, PNG, BMP, TIFF (max 200MB)
        3. **📏 Qualité recommandée** : Minimum 224x224 pixels, bien éclairée
        4. **🚀 Lancez l'analyse** avec le bouton d'analyse
        5. **📊 Consultez les résultats** détaillés et choisissez votre méthode
        
        ### 🎯 Que fait cette analyse ?
        
        - **Classification** : Détermine si l'image contient des fissures
        - **Segmentation** : Localise précisément les fissures détectées  
        - **Quantification** : Calcule la surface et les métriques
        """)

    # Pas de persistance d'encart supplémentaire; l'UI reste telle quelle sans rerun
    
    # Affichage du footer
    show_footer()

if __name__ == "__main__":
    main()