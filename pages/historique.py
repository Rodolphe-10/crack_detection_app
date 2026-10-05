#!/usr/bin/env python3
"""
📜 Historique des Analyses
-------------------------

Page Streamlit affichant l'historique unifié de toutes les analyses
(simple, temps réel, batch). Permet filtrage, export CSV et purge.
"""

import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from config.config import StreamlitConfig
from utils.sidebar import show_unified_sidebar
from utils.history_store import fetch_history, export_history_csv, clear_history


def setup_page():
    st.set_page_config(**StreamlitConfig.PAGE_CONFIG)
    show_unified_sidebar("Historique")



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


def to_dataframe(rows):
    df = pd.DataFrame(rows)
    if not df.empty:
        df["datetime"] = df["timestamp"].apply(lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)))
        df["fissure"] = df["has_crack"].map({True: "Oui", False: "Non"})
        df["confiance_%"] = (df["confidence"].astype(float) * 100).round(1)
        df = df[[
            "id", "datetime", "page", "method", "fissure", "confiance_%", "analysis_time", "filename", "extra"
        ]]
        df = df.rename(columns={
            "datetime": "Horodatage",
            "page": "Page",
            "method": "Méthode",
            "fissure": "Fissure",
            "confiance_%": "Confiance (%)",
            "analysis_time": "Durée (s)",
            "filename": "Fichier",
            "extra": "Détails",
        })
    return df


def main():
    setup_page()
    st.markdown("# 📜 Historique des Analyses")
    st.info("Vue consolidée de toutes les analyses effectuées dans l'application.")

    # Filtres
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        page = st.selectbox("Page", options=["Toutes", "simple", "realtime", "batch"], index=0)
    with col_f2:
        method = st.selectbox("Méthode", options=["Toutes", "upload", "webcam", "batch"], index=0)
    with col_f3:
        crack_filter = st.selectbox("Fissure", options=["Toutes", "Oui", "Non"], index=0)
    with col_f4:
        limit = st.number_input("Limite", min_value=50, max_value=10000, value=500, step=50)

    kwargs = {}
    if page != "Toutes":
        kwargs["page"] = page
    if method != "Toutes":
        kwargs["method"] = method
    if crack_filter != "Toutes":
        kwargs["has_crack"] = (crack_filter == "Oui")

    rows = fetch_history(limit=int(limit), **kwargs)
    df = to_dataframe(rows)

    st.markdown("### 📊 Tableau")
    st.dataframe(df, use_container_width=True)

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.download_button(
            label="🧾 Exporter CSV",
            data=export_history_csv(limit=int(limit)),
            file_name=f"historique_analyses_{int(time.time())}.csv",
            mime="text/csv",
            key="download_history_csv",
        )
    with col_b2:
        st.caption(f"Entrées: {len(df)}")
    with col_b3:
        if st.button("🗑️ Vider l'historique", help="Supprime définitivement toutes les entrées"):
            clear_history()
            st.success("Historique vidé.")
            st.rerun()


if __name__ == "__main__":
    main()


