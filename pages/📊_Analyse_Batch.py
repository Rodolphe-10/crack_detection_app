#!/usr/bin/env python3
"""
📊 Analyse Batch
---------------

Page pour analyser plusieurs images en lot et générer des rapports consolidés.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

from config.config import AppConfig, StreamlitConfig
from utils.model_loader import load_models, setup_device
from utils.image_processor import (
    preprocess_image_for_classification,
    run_classification_analysis,
    run_opencv_segmentation,
    validate_image_for_analysis,
)
from utils.validation_simple import validate_image_for_analysis_simple
from utils.sidebar import show_unified_sidebar, show_footer
from utils.history_store import log_analysis


def setup_page():
    """Configure la page."""
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    show_unified_sidebar("Analyse Batch")
    


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




def analyze_single_image(image_path: str, classification_model, device) -> Dict[str, Any]:
    """Analyse une image individuelle."""
    try:
        # Charger l'image
        image = Image.open(image_path)
        image_np = np.array(image)
        
        # Validation dédiée, plus permissive pour Batch
        is_valid, validation_msg = validate_image_for_analysis_simple(image_np)
        if not is_valid:
            return {
                "filename": os.path.basename(image_path),
                "valid": False,
                "error": validation_msg,
                "has_crack": None,
                "confidence": None,
                "analysis_time": None,
            }
        
        # Analyse
        start_time = time.time()
        result = run_classification_analysis(classification_model, image_np)
        
        if result is None:
            return {
                "filename": os.path.basename(image_path),
                "valid": False,
                "error": "Échec de l'analyse",
                "has_crack": None,
                "confidence": None,
                "analysis_time": None,
            }
        
        pred_class, confidence, _ = result
        
        # Vérification supplémentaire des valeurs
        if pred_class is None or confidence is None:
            return {
                "filename": os.path.basename(image_path),
                "valid": False,
                "error": "Résultats de classification invalides",
                "has_crack": None,
                "confidence": None,
                "analysis_time": None,
            }
        
        analysis_time = time.time() - start_time
        
        # Segmentation si fissure détectée
        mask = None
        if pred_class == 1:
            mask = run_opencv_segmentation(image_np)
        
        return {
            "filename": os.path.basename(image_path),
            "valid": True,
            "error": None,
            "has_crack": bool(pred_class == 1),
            "confidence": float(confidence),
            "analysis_time": float(analysis_time),
            "pred_class": int(pred_class) if pred_class is not None else -1,
            "has_mask": mask is not None,
            "mask_area": float(np.sum(mask > 0) / mask.size * 100) if mask is not None else None,
        }
        
    except Exception as e:
        return {
            "filename": os.path.basename(image_path),
            "valid": False,
            "error": str(e),
            "has_crack": None,
            "confidence": None,
            "analysis_time": None,
        }


def main():
    """Fonction principale."""
    setup_page()
    
    st.markdown("# 📊 Analyse Batch")
    st.markdown("Analysez plusieurs images en lot et générez des rapports consolidés.")
    
    # Upload multiple files
    uploaded_files = st.file_uploader(
        "Sélectionnez plusieurs images...",
        type=['jpg', 'jpeg', 'png', 'bmp'],
        accept_multiple_files=True,
        key="batch_upload"
    )
    
    if not uploaded_files:
        st.info("💡 Uploadez plusieurs images pour commencer l'analyse batch.")
        return
    
    st.success(f"📁 {len(uploaded_files)} images sélectionnées")
    
    # Options d'analyse
    col1, col2 = st.columns(2)
    with col1:
        include_segmentation = st.checkbox("🔍 Inclure segmentation", value=True)
    with col2:
        save_individual_results = st.checkbox("💾 Sauvegarder résultats individuels", value=True)
    
    # Bouton d'analyse
    if st.button("🚀 Lancer l'Analyse Batch", type="primary", key="batch_analyze_btn"):
        if not uploaded_files:
            st.error("❌ Aucune image sélectionnée")
            return
        
        # Charger les modèles
        with st.spinner("🔄 Chargement des modèles..."):
            (classification_model, segmentation_model), device = load_models(), setup_device()
            
            if classification_model is None:
                st.error("❌ Impossible de charger les modèles")
                return
        
        # Créer un dossier temporaire pour les images
        temp_dir = Path("temp_batch_analysis")
        temp_dir.mkdir(exist_ok=True)
        
        # Sauvegarder les images uploadées
        image_paths = []
        for uploaded_file in uploaded_files:
            temp_path = temp_dir / uploaded_file.name
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_paths.append(str(temp_path))
        
        # Analyse batch
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, image_path in enumerate(image_paths):
            status_text.text(f"Analyse de {os.path.basename(image_path)}... ({i+1}/{len(image_paths)})")
            
            result = analyze_single_image(image_path, classification_model, device)
            results.append(result)
            
            # Journaliser dans l'historique
            if result["valid"]:
                try:
                    log_analysis(
                        page="batch",
                        method="upload",
                        has_crack=result["has_crack"],
                        confidence=result["confidence"],
                        analysis_time=result["analysis_time"],
                        filename=result["filename"],
                        extra={
                            "pred_class": result["pred_class"],
                            "has_mask": result["has_mask"],
                            "mask_area": result["mask_area"],
                            "batch_index": i,
                            "total_in_batch": len(image_paths),
                        }
                    )
                except Exception as e:
                    st.warning(f"⚠️ Erreur journalisation: {e}")
            
            progress_bar.progress((i + 1) / len(image_paths))
        
        # Nettoyer les fichiers temporaires
        for path in image_paths:
            try:
                os.remove(path)
            except:
                pass
        try:
            temp_dir.rmdir()
        except:
            pass
        
        # Résultats
        st.success("✅ Analyse batch terminée !")
        
        # Statistiques
        valid_results = [r for r in results if r["valid"]]
        invalid_results = [r for r in results if not r["valid"]]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(results))
        with col2:
            st.metric("Valides", len(valid_results))
        with col3:
            if valid_results:
                crack_count = sum(1 for r in valid_results if r["has_crack"])
                st.metric("Fissures", f"{crack_count}/{len(valid_results)}")
        with col4:
            if valid_results:
                avg_confidence = np.mean([r["confidence"] for r in valid_results])
                st.metric("Confiance Moy.", f"{avg_confidence:.1%}")
        
        # Tableau des résultats
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h3 style="color: white; margin: 0;">📋 Résultats Détaillés</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if valid_results:
            df = pd.DataFrame(valid_results)
            df["Fissure"] = df["has_crack"].map({True: "Oui", False: "Non"})
            df["Confiance (%)"] = (df["confidence"] * 100).round(1)
            df["Durée (s)"] = df["analysis_time"].round(2)
            
            # Formater la surface fissurée en pourcentage
            if "mask_area" in df.columns:
                df["Surface Fissurée (%)"] = df["mask_area"].apply(lambda x: f"{x:.2f}%" if x is not None else "N/A")
            display_df = df[[
                "filename", "Fissure", "Confiance (%)", "Durée (s)", "has_mask", "Surface Fissurée (%)"
            ]].rename(columns={
                "filename": "Fichier",
                "has_mask": "Segmentation"
            })
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export CSV
            csv_data = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="🧾 Exporter CSV",
                data=csv_data,
                file_name=f"resultats_batch_{int(time.time())}.csv",
                mime="text/csv",
                key="download_batch_csv"
            )
        
        if invalid_results:
            st.markdown("### ⚠️ Images Non Valides")
            invalid_df = pd.DataFrame(invalid_results)
            st.dataframe(invalid_df[["filename", "error"]], use_container_width=True)
    
    # Affichage du footer
    show_footer()


if __name__ == "__main__":
    main()