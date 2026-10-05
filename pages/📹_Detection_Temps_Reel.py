#!/usr/bin/env python3
"""
Page de Détection en Temps Réel
===============================

Interface pour la détection de fissures en temps réel
via webcam avec analyse continue.
"""

import streamlit as st
import cv2
import numpy as np
import time
from PIL import Image
import torch
import torch.nn.functional as F
from pathlib import Path
import sys
import threading
import queue

# Ajouter le répertoire parent au path pour les imports
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from config.config import AppConfig, StreamlitConfig
from utils.model_loader import load_models, setup_device
from utils.image_processor import (
    preprocess_image_for_classification,
    postprocess_segmentation_mask,
    create_enhanced_overlay,
    calculate_crack_statistics,
    get_validation_details,
    validate_image_for_analysis
)
from utils.chat_assistant import show_chat_widget, get_context_for_page
from utils.sidebar import show_unified_sidebar, show_footer
from utils.history_store import log_analysis

# Essayer d'importer streamlit-webrtc
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ImportError:
    WEBRTC_AVAILABLE = False

def setup_page():
    """Configure la page (doit être le premier appel Streamlit)."""
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    show_unified_sidebar("Détection Temps Réel")



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



    
    # Préserver la position de scroll de la page principale
    st.markdown("""
    <script>
    (function(){
        const key = 'realtime_page_scrollY';
        function restore(){
            try{
                const top = parseFloat(localStorage.getItem(key) || '0');
                if(!isNaN(top)) { window.scrollTo(0, top); }
            }catch(e){}
        }
        function listen(){
            try{
                window.addEventListener('scroll', () => {
                    try{ localStorage.setItem(key, window.scrollY || 0); }catch(e){}
                }, {passive:true});
            }catch(e){}
        }
        restore();
        setTimeout(restore, 100);
        setTimeout(restore, 500);
        listen();
    })();
    </script>
    """, unsafe_allow_html=True)

class RealTimeAnalyzer:
    """Analyseur en temps réel pour les flux vidéo."""
    
    def __init__(self, classification_model, segmentation_model, device):
        self.classification_model = classification_model
        self.segmentation_model = segmentation_model
        self.device = device
        self.analysis_interval = 2.0  # Analyser toutes les 2 secondes
        self.last_analysis_time = 0
        self.current_result = None
        self.frame_count = 0
        
    def analyze_frame(self, frame):
        """Analyse une frame vidéo."""
        current_time = time.time()
        
        # Limiter la fréquence d'analyse
        if current_time - self.last_analysis_time < self.analysis_interval:
            return self.current_result
        
        try:
            # Préprocessing
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_tensor = preprocess_image_for_classification(frame_rgb)
            
            # Classification
            self.classification_model.eval()
            with torch.no_grad():
                image_tensor_device = image_tensor.to(self.device)
                outputs = self.classification_model(image_tensor_device)
                probabilities = F.softmax(outputs, dim=1)
                predicted_class = torch.argmax(outputs, dim=1)
                confidence = torch.max(probabilities, dim=1)[0]
            
            classification_result = (
                predicted_class.item(),
                confidence.item(),
                probabilities.cpu().numpy()[0]
            )
            
            # Segmentation si fissure détectée
            mask = None
            statistics = {}
            
            if predicted_class.item() == 1:  # Fissure détectée
                self.segmentation_model.eval()
                with torch.no_grad():
                    seg_outputs = self.segmentation_model(image_tensor_device)
                    mask_tensor = torch.sigmoid(seg_outputs)
                    mask = (mask_tensor > 0.5).float().squeeze().cpu().numpy()
                
                # Redimensionner le masque
                mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
                
                # Calculer les statistiques
                statistics = calculate_crack_statistics(mask, frame.shape[:2])
            
            self.current_result = {
                'classification': classification_result,
                'mask': mask,
                'statistics': statistics,
                'timestamp': current_time
            }
            
            self.last_analysis_time = current_time
            
        except Exception as e:
            st.error(f"Erreur d'analyse: {e}")
        
        return self.current_result
    
    def overlay_results(self, frame, result):
        """Ajoute les résultats d'analyse sur la frame."""
        if result is None:
            return frame
        
        frame_with_overlay = frame.copy()
        
        # Ajouter le masque si disponible
        if result['mask'] is not None:
            overlay = create_enhanced_overlay(frame_with_overlay, result['mask'], alpha=0.4)
            frame_with_overlay = overlay
        
        # Ajouter les informations textuelles
        pred_class, confidence, _ = result['classification']
        class_name = AppConfig.CLASSIFICATION_CLASSES[pred_class]
        
        # Couleur du texte selon le résultat
        color = (0, 0, 255) if pred_class == 1 else (0, 255, 0)  # Rouge si fissure, vert sinon
        
        # Texte principal
        text = f"{class_name}: {confidence:.1%}"
        cv2.putText(frame_with_overlay, text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Statistiques si fissure détectée
        if pred_class == 1 and result['statistics']:
            stats = result['statistics']
            y_offset = 70
            
            stats_text = [
                f"Surface: {stats.get('total_area_mm2', 0):.1f} mm²",
                f"Densite: {stats.get('crack_density', 0):.2f}%",
                f"Severite: {stats.get('severity_level', 'N/A')}"
            ]
            
            for i, stat_text in enumerate(stats_text):
                cv2.putText(frame_with_overlay, stat_text, (10, y_offset + i * 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        
        # Timestamp
        timestamp = time.strftime("%H:%M:%S", time.localtime(result['timestamp']))
        cv2.putText(frame_with_overlay, f"Analyse: {timestamp}", (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame_with_overlay

def create_video_processor(classification_model, segmentation_model, device):
    """Crée un processeur vidéo pour streamlit-webrtc."""
    
    analyzer = RealTimeAnalyzer(classification_model, segmentation_model, device)
    
    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Analyser la frame
        result = analyzer.analyze_frame(img)
        
        # Ajouter les overlays
        processed_frame = analyzer.overlay_results(img, result)
        
        return av.VideoFrame.from_ndarray(processed_frame, format="bgr24")
    
    return video_frame_callback

def show_realtime_detection():
    """Interface de détection en temps réel avec localisation."""
    st.markdown("### 🎥 Détection Temps Réel avec Localisation")
    
    # Contrôles de la détection
    col_control1, col_control2, col_control3 = st.columns(3)
    
    with col_control1:
        enable_detection = st.checkbox("🔍 Activer Détection", value=True, key="realtime_enable_detection")
    
    with col_control2:
        show_overlay = st.checkbox("📍 Localisation Visible", value=True, key="realtime_show_overlay")
    
    with col_control3:
        detection_sensitivity = st.slider("Sensibilité", 0.3, 0.9, 0.5, 0.1, key="realtime_sensitivity")
    
    # Initialiser les modèles avec cache
    @st.cache_resource
    def load_rt_models():
        """Charge les modèles avec cache pour éviter les rechargements."""
        return load_models(), setup_device()
    
    if "rt_models_loaded" not in st.session_state:
        with st.spinner("🔄 Chargement des modèles..."):
            (classification_model, segmentation_model), device = load_rt_models()
            
            if classification_model and segmentation_model:
                st.session_state.rt_analyzer = RealTimeAnalyzer(classification_model, segmentation_model, device)
                st.session_state.rt_models_loaded = True
                st.success("✅ Modèles chargés - Détection temps réel prête !")
            else:
                st.error("❌ Impossible de charger les modèles")
                return
    
    # Placeholders pour l'affichage temps réel
    video_placeholder = st.empty()
    results_placeholder = st.empty()
    metrics_placeholder = st.empty()
    
    # Contrôles de capture avec clés uniques
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        start_button = st.button("▶️ Démarrer", type="primary", key="realtime_start_btn")
    
    with col_btn2:
        stop_button = st.button("⏹️ Arrêter", key="realtime_stop_btn")
    
    with col_btn3:
        capture_button = st.button("📸 Capturer", key="realtime_capture_btn")
    
    # Gestion de l'état de la webcam avec clés uniques
    if "realtime_webcam_active" not in st.session_state:
        st.session_state.realtime_webcam_active = False
    
    if start_button:
        st.session_state.realtime_webcam_active = True
        
    if stop_button:
        st.session_state.realtime_webcam_active = False
        # Nettoyer la webcam quand elle est arrêtée
        if "realtime_cap" in st.session_state and st.session_state.realtime_cap is not None:
            st.session_state.realtime_cap.release()
            st.session_state.realtime_cap = None
        st.success("✅ Webcam arrêtée")
        st.rerun()
    
    # Boucle de détection temps réel
    if st.session_state.realtime_webcam_active and st.session_state.get("rt_models_loaded", False):
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                st.error("❌ Impossible d'accéder à la webcam")
                st.session_state.webcam_active = False
                return
            
            frame_count = 0
            detection_history = []
            is_valid = True  # Initialiser la variable de validation
            
            # Boucle principale de détection
            while st.session_state.realtime_webcam_active:
                ret, frame = cap.read()
                
                if not ret:
                    st.warning("⚠️ Impossible de lire la frame de la webcam")
                    break
                
                frame_count += 1
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Analyser seulement toutes les 5 frames pour les performances
                if enable_detection and frame_count % 5 == 0:
                    try:
                        # Validation rapide de la surface en temps réel
                        try:
                            is_valid, validation_msg = validate_image_for_analysis(frame_rgb, strict_validation=True)
                        except Exception as e:
                            # En cas d'erreur de validation, continuer l'analyse
                            is_valid = True
                            validation_msg = f"Validation ignorée (erreur: {str(e)})"
                        
                        # Afficher le statut de validation
                        with results_placeholder.container():
                            if is_valid:
                                st.success(f"✅ {validation_msg}")
                            else:
                                st.warning(f"⚠️ Surface non optimale: {validation_msg}")
                                st.info("💡 Pointez la caméra vers une surface en béton pour de meilleurs résultats")
                                # Passer à la frame suivante sans analyser
                                continue
                        
                        # Analyse avec le modèle
                        result = st.session_state.rt_analyzer.analyze_frame(frame)
                        
                        if result:
                            pred_class, confidence, _ = result['classification']
                            
                            # Ajouter à l'historique local
                            detection_history.append({
                                'frame': frame_count,
                                'has_crack': pred_class == 1,
                                'confidence': confidence,
                                'timestamp': time.time()
                            })
                            
                            # Journaliser dans l'historique global (toutes les 10 frames)
                            if frame_count % 10 == 0:
                                try:
                                    log_analysis(
                                        page="realtime",
                                        method="webcam",
                                        has_crack=bool(pred_class == 1),
                                        confidence=float(confidence),
                                        analysis_time=None,  # Pas de mesure de temps en temps réel
                                        filename=None,
                                        extra={
                                            "frame": frame_count,
                                            "has_mask": result.get('mask') is not None,
                                            "detection_sensitivity": float(detection_sensitivity),
                                        }
                                    )
                                except Exception as e:
                                    pass  # Ignorer les erreurs de journalisation en temps réel
                            
                            # Garder seulement les 10 dernières détections
                            if len(detection_history) > 10:
                                detection_history.pop(0)
                            
                            # Appliquer la localisation si fissure détectée
                            if pred_class == 1 and confidence > detection_sensitivity and show_overlay:
                                if result.get('mask') is not None:
                                    # Créer l'overlay avec localisation
                                    frame_with_overlay = st.session_state.rt_analyzer.overlay_results(frame_rgb, result)
                                    
                                    # Ajouter les informations de détection
                                    cv2.putText(frame_with_overlay, f"FISSURE DETECTEE", (10, 30),
                                              cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                                    cv2.putText(frame_with_overlay, f"Confiance: {confidence:.1%}", (10, 70),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                                    
                                    frame_rgb = frame_with_overlay
                            
                            # Mettre à jour les résultats en temps réel
                            with results_placeholder.container():
                                if pred_class == 1 and confidence > detection_sensitivity:
                                    st.error(f"⚠️ **FISSURE DÉTECTÉE** - Confiance: {confidence:.1%}")
                                else:
                                    st.success(f"✅ Structure Saine - Confiance: {confidence:.1%}")
                            
                            # Afficher les métriques temps réel
                            with metrics_placeholder.container():
                                if len(detection_history) > 1:
                                    recent_detections = sum(1 for d in detection_history if d['has_crack'])
                                    crack_confidences = [d['confidence'] for d in detection_history if d['has_crack']]
                                    if len(crack_confidences) > 0:
                                        avg_confidence = float(np.mean(crack_confidences))
                                    else:
                                        avg_confidence = float(np.mean([d['confidence'] for d in detection_history]))
                                    
                                    col_m1, col_m2, col_m3 = st.columns(3)
                                    with col_m1:
                                        st.metric("Détections", f"{recent_detections}/10")
                                    with col_m2:
                                        st.metric("Confiance Moy.", f"{avg_confidence:.1%}")
                                    with col_m3:
                                        st.metric("Frame", frame_count)
                    
                    except Exception as e:
                        st.warning(f"Erreur d'analyse: {e}")
                
                # Ajouter un indicateur de validation sur la frame
                frame_with_validation = frame_rgb.copy()
                
                # Ajouter un indicateur de validation en haut à droite
                validation_color = (0, 255, 0) if is_valid else (0, 0, 255)  # Vert si valide, rouge sinon
                validation_text = "VALID" if is_valid else "INVALID"
                cv2.putText(frame_with_validation, validation_text, (frame_with_validation.shape[1] - 120, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, validation_color, 2)
                
                # Ajouter un cercle de statut
                cv2.circle(frame_with_validation, (frame_with_validation.shape[1] - 30, 30), 10, validation_color, -1)
                
                # Afficher la frame (avec ou sans overlay)
                with video_placeholder.container():
                    st.image(frame_with_validation, caption="🎥 Flux Temps Réel", use_container_width=True)
                
                # Pause courte pour éviter la surcharge
                time.sleep(0.1)
                
                # Vérifier si l'utilisateur veut arrêter
                if not st.session_state.realtime_webcam_active:
                    break
            
            cap.release()
            
        except Exception as e:
            st.error(f"❌ Erreur de la webcam: {e}")
            st.session_state.realtime_webcam_active = False
            
    elif st.session_state.realtime_webcam_active and not st.session_state.get("rt_models_loaded", False):
        st.warning("⚠️ Modèles non chargés - Impossible de démarrer la détection")
        st.session_state.realtime_webcam_active = False

def show_manual_capture_interface():
    """Interface pour la capture manuelle d'images via webcam."""
    st.markdown("### 📸 Capture Manuelle")
    st.markdown("Capturez une image via webcam et analysez-la immédiatement.")
    
    # Initialiser la webcam
    if 'manual_cap' not in st.session_state:
        st.session_state.manual_cap = None
    
    # Boutons de contrôle
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎥 Démarrer Webcam", key="start_manual_cam"):
            try:
                # Libérer la webcam précédente si elle existe
                if st.session_state.manual_cap:
                    st.session_state.manual_cap.release()
                
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    st.session_state.manual_cap = cap
                    st.success("✅ Webcam démarrée")
                    st.rerun()
                else:
                    st.error("❌ Impossible d'accéder à la webcam")
            except Exception as e:
                st.error(f"❌ Erreur webcam: {e}")
    
    with col2:
        if st.button("📸 Capturer", key="capture_manual", disabled=st.session_state.manual_cap is None):
            if st.session_state.manual_cap:
                try:
                    ret, frame = st.session_state.manual_cap.read()
                    if ret:
                        # Convertir BGR en RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        st.session_state.manual_captured_frame = frame_rgb
                        st.success("✅ Image capturée !")
                        st.rerun()
                    else:
                        st.error("❌ Échec de la capture")
                except Exception as e:
                    st.error(f"❌ Erreur de capture: {e}")
    
    with col3:
        if st.button("🛑 Arrêter Webcam", key="stop_manual_cam"):
            if st.session_state.manual_cap:
                st.session_state.manual_cap.release()
                st.session_state.manual_cap = None
                st.success("✅ Webcam arrêtée")
                st.rerun()
                
                # Afficher l'image capturée
    if 'manual_captured_frame' in st.session_state:
        st.markdown("### 🖼️ Image Capturée")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(st.session_state.manual_captured_frame, caption="Image Capturée", use_container_width=True)
        
        with col2:
            st.markdown("#### 🔍 Analyse de l'Image")
            
            # Validation de l'image
            with st.spinner("🔍 Validation de l'image..."):
                try:
                    is_valid, validation_msg = validate_image_for_analysis(st.session_state.manual_captured_frame, strict_validation=True)
                except Exception as e:
                    # En cas d'erreur de validation, considérer comme valide
                    is_valid = True
                    validation_msg = f"Validation ignorée (erreur: {str(e)})"
                
                if is_valid:
                    st.success(validation_msg)
                else:
                    st.warning(f"⚠️ {validation_msg}")
                    st.info("💡 L'analyse peut quand même être lancée, mais les résultats peuvent être moins fiables.")
                
                # Bouton d'analyse (toujours disponible)
                if st.button("🚀 Lancer l'Analyse", type="primary", key="analyze_manual_capture"):
                    with st.spinner("🧠 Analyse en cours..."):
                        try:
                            # Charger les modèles
                            classification_model, segmentation_model = load_models()
                            device = setup_device()
                            
                            if classification_model and segmentation_model:
                                # Préparer l'image pour l'analyse
                                frame_bgr = cv2.cvtColor(st.session_state.manual_captured_frame, cv2.COLOR_RGB2BGR)
                                
                                # Créer l'analyseur
                                analyzer = RealTimeAnalyzer(classification_model, segmentation_model, device)
                                
                                # Analyser l'image
                                result = analyzer.analyze_frame(frame_bgr)
                                
                                if result:
                                    # Afficher les résultats
                                    st.markdown("#### 📊 Résultats de l'Analyse")
                                    
                                    pred_class, confidence, _ = result['classification']
                                    class_name = AppConfig.CLASSIFICATION_CLASSES[pred_class]
                                    
                                    col_r1, col_r2 = st.columns(2)
                                    
                                    with col_r1:
                                        if pred_class == 1:
                                            st.error(f"⚠️ **{class_name}** détectée")
                                            st.metric("Confiance", f"{confidence:.1%}")
                                            st.metric("Statut", "⚠️ Fissure", delta="Inspection requise")
                                        else:
                                            st.success(f"✅ **{class_name}**")
                                            st.metric("Confiance", f"{confidence:.1%}")
                                            st.metric("Statut", "✅ Sain", delta="Aucune action")
                                    
                                    with col_r2:
                                        # Afficher l'overlay si disponible
                                        if result.get('mask') is not None:
                                            overlay_frame = analyzer.overlay_results(st.session_state.manual_captured_frame, result)
                                            st.image(overlay_frame, caption="Analyse avec Localisation", use_container_width=True)
                                    
                                    # Journaliser l'analyse
                                    try:
                                        log_analysis(
                                            page="realtime",
                                            method="manual_capture",
                                            has_crack=bool(pred_class == 1),
                                            confidence=float(confidence),
                                            analysis_time=None,
                                            filename=f"manual_capture_{int(time.time())}.jpg",
                                            extra={
                                                "has_mask": result.get('mask') is not None,
                                                "capture_method": "webcam"
                                            }
                                        )
                                    except Exception as e:
                                        st.warning(f"⚠️ Impossible d'enregistrer l'analyse: {e}")
                                    
                                else:
                                    st.error("❌ Échec de l'analyse")
                                    
                            else:
                                st.error("❌ Modèles non disponibles")
                                
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'analyse: {e}")
                            st.exception(e)  # Afficher la trace complète pour le débogage
    
    # Instructions d'utilisation
    if st.session_state.manual_cap is None:
        st.info("💡 **Instructions :** Cliquez sur 'Démarrer Webcam' pour commencer la capture manuelle.")
    else:
        st.info("💡 **Instructions :** Pointez la caméra vers une surface en béton et cliquez sur 'Capturer'.")
    
    # Nettoyer la webcam à la fermeture de la page
    if st.session_state.manual_cap and not st.session_state.get("manual_cap_active", False):
        st.session_state.manual_cap.release()
        st.session_state.manual_cap = None

def show_upload_for_realtime():
    """Interface pour upload d'image pour simulation temps réel."""
    st.markdown("### 📤 Simulation Temps Réel")
    st.info("💡 Uploadez une image pour simuler une analyse en temps réel")
    
    uploaded_file = st.file_uploader(
        "Choisissez une image pour simulation...",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        key="realtime_simulation_upload"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_np = np.array(image)
        
        # Validation de l'image
        st.markdown("### 🔍 Validation de l'Image")
        with st.spinner("🔍 Validation de l'image..."):
            try:
                is_valid, validation_msg = validate_image_for_analysis(image_np, strict_validation=True)
            except Exception as e:
                # En cas d'erreur de validation, considérer comme valide
                is_valid = True
                validation_msg = f"Validation ignorée (erreur: {str(e)})"
            
            if is_valid:
                st.success(validation_msg)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(image, caption="Image Originale", use_container_width=True)
        
        with col2:
            if st.button("🔄 Simulation Temps Réel", type="primary", key="realtime_simulation_btn"):
                # Charger les modèles
                classification_model, segmentation_model = load_models()
                device = setup_device()
                
                if classification_model and segmentation_model:
                    analyzer = RealTimeAnalyzer(classification_model, segmentation_model, device)
                    
                    # Simuler plusieurs analyses avec légères variations
                    placeholder = st.empty()
                    
                    for i in range(5):
                        with placeholder.container():
                            st.write(f"📊 Analyse #{i+1}/5")
                            
                            # Ajouter un peu de bruit pour simuler des conditions réelles
                            noise = np.random.normal(0, 5, image_np.shape).astype(np.uint8)
                            noisy_image = np.clip(image_np.astype(int) + noise, 0, 255).astype(np.uint8)
                            
                            # Analyser
                            if len(noisy_image.shape) == 3:
                                frame_bgr = cv2.cvtColor(noisy_image, cv2.COLOR_RGB2BGR)
                            else:
                                frame_bgr = noisy_image
                            
                            result = analyzer.analyze_frame(frame_bgr)
                            
                            if result:
                                # Afficher avec overlay
                                processed_frame = analyzer.overlay_results(noisy_image, result)
                                st.image(processed_frame, caption=f"Analyse Temps Réel #{i+1}", use_container_width=True)
                                
                                # Résultats
                                pred_class, confidence, _ = result['classification']
                                class_name = AppConfig.CLASSIFICATION_CLASSES[pred_class]
                                
                                if pred_class == 1:
                                    st.error(f"⚠️ {class_name} (Confiance: {confidence:.1%})")
                                else:
                                    st.success(f"✅ {class_name} (Confiance: {confidence:.1%})")
                            
                            time.sleep(1)  # Pause entre les analyses
                else:
                    st.error("❌ Modèles non disponibles")
                
                # Afficher l'image même si invalide pour référence
                st.image(image, caption="Image (Non valide)", use_container_width=True)

def main():
    """Fonction principale de la page."""
    setup_page()
    
    st.markdown("# 📹 Détection en Temps Réel")
    st.markdown("Analysez en temps réel via webcam ou simulez avec vos images.")
    
    # Widget de chat (optionnel) avec clé unique
    try:
        show_chat_widget("realtime", get_context_for_page("detection_temps_reel"))
    except Exception:
        pass
    
    # Modes disponibles
    st.markdown("### 📱 Modes Disponibles")
    mode = st.radio(
        "Choisissez un mode:",
        ["🎥 Temps Réel avec Localisation", "📸 Capture Manuelle", "📤 Simulation avec Upload"],
        help="Différentes méthodes pour la détection en temps réel",
        index=0,
        key="realtime_mode_selector"
    )
    
    # Utiliser des clés uniques pour éviter les doublons
    if mode == "🎥 Temps Réel avec Localisation":
        show_realtime_detection()
    elif mode == "📸 Capture Manuelle":
        show_manual_capture_interface()
    elif mode == "📤 Simulation avec Upload":
        show_upload_for_realtime()
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()