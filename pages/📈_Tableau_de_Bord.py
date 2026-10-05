#!/usr/bin/env python3
"""
Page Tableau de Bord - Statistiques et Historique
===============================================

Cette page affiche l'historique des analyses et les statistiques
globales de l'application.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sys
import time
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Ajouter le répertoire parent au path
current_dir = Path(__file__).parent.parent
sys.path.append(str(current_dir))

from utils.sidebar import show_unified_sidebar

# Configuration de la page
st.set_page_config(
    page_title="📈 Tableau de Bord",
    page_icon="📈",
    layout="wide"
)

def setup_page():
    """Configure la page et l'en-tête."""
    show_unified_sidebar("Tableau de Bord")



    # CSS pour masquer la sidebar automatique de Streamlit
    st.markdown("""
    <style>
    /* Masquer les éléments automatiques de la sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
    section[data-testid="stSidebar"] [data-testid="stSidebarSearch"],
    section[data-testid="stSidebar"] [data-testid="stSidebarHistory"],
    section[data-testid="stSidebar"] [data-testid="stSidebarMenu"] {
        display: none !important;
    }
    
    /* Masquer le contenu automatique mais préserver la scrollbar et le bouton de fermeture */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > div:not([data-testid="stSidebarUserContent"]):not([data-testid="stSidebarCloseButton"]) {
        display: none !important;
    }
    
    /* S'assurer que le bouton de fermeture reste visible */
    section[data-testid="stSidebar"] [data-testid="stSidebarCloseButton"],
    section[data-testid="stSidebar"] button[aria-label*="Close"],
    section[data-testid="stSidebar"] button[aria-label*="Fermer"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 9999 !important;
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
    </style>
    """, unsafe_allow_html=True)



    
    st.markdown("# 📈 Tableau de Bord")
    st.markdown("### Historique des analyses et statistiques globales")
    
    # Appliquer le style personnalisé
    st.markdown("""
    <style>
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def generate_sample_data():
    """Génère des données d'exemple pour la démonstration."""
    np.random.seed(42)
    
    # Générer 30 jours de données
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    
    data = []
    for date in dates:
        # Nombre d'analyses par jour (1-20)
        num_analyses = np.random.randint(1, 21)
        
        for i in range(num_analyses):
            # Simulation de résultats d'analyse
            has_crack = np.random.choice([0, 1], p=[0.7, 0.3])  # 30% de chance d'avoir des fissures
            confidence = np.random.uniform(0.6, 0.99) if has_crack else np.random.uniform(0.7, 0.95)
            
            # Surface fissurée (si fissure détectée)
            crack_surface = np.random.uniform(0.5, 15.0) if has_crack else 0.0
            
            # Méthode utilisée
            method = np.random.choice(['Deep Learning', 'OpenCV'], p=[0.7, 0.3])
            
            # Temps de traitement
            processing_time = np.random.uniform(1.5, 4.5)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'datetime': date + timedelta(hours=np.random.randint(8, 18), 
                                           minutes=np.random.randint(0, 60)),
                'has_crack': has_crack,
                'confidence': confidence,
                'crack_surface': crack_surface,
                'method': method,
                'processing_time': processing_time,
                'image_name': f"image_{i+1}_{date.strftime('%m%d')}.jpg"
            })
    
    return pd.DataFrame(data)

def show_metrics_overview(df):
    """Affiche les métriques principales."""
    st.markdown("## 📊 Vue d'Ensemble")
    
    # Calculs des métriques
    total_analyses = len(df)
    total_cracks = df['has_crack'].sum()
    crack_rate = (total_cracks / total_analyses) * 100 if total_analyses > 0 else 0
    avg_confidence = df['confidence'].mean() * 100
    avg_processing_time = df['processing_time'].mean()
    
    # Affichage des métriques en colonnes
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📋 Total Analyses",
            value=f"{total_analyses:,}",
            delta=f"+{np.random.randint(5, 15)} cette semaine"
        )
    
    with col2:
        st.metric(
            label="⚠️ Fissures Détectées",
            value=f"{total_cracks:,}",
            delta=f"{crack_rate:.1f}% du total"
        )
    
    with col3:
        st.metric(
            label="🎯 Confiance Moyenne",
            value=f"{avg_confidence:.1f}%",
            delta="Excellente précision"
        )
    
    with col4:
        st.metric(
            label="⚡ Temps Moyen",
            value=f"{avg_processing_time:.1f}s",
            delta="Performance optimale"
        )
    
    with col5:
        st.metric(
            label="🧠 Deep Learning",
            value=f"{(df['method'] == 'Deep Learning').sum():,}",
            delta=f"{((df['method'] == 'Deep Learning').sum() / total_analyses * 100):.1f}% du total"
        )

def show_time_series_charts(df):
    """Affiche les graphiques temporels."""
    st.markdown("## 📈 Évolution Temporelle")
    
    # Préparer les données par jour
    daily_stats = df.groupby('date').agg({
        'has_crack': ['count', 'sum'],
        'confidence': 'mean',
        'processing_time': 'mean'
    }).round(2)
    
    daily_stats.columns = ['total_analyses', 'cracks_found', 'avg_confidence', 'avg_processing_time']
    daily_stats = daily_stats.reset_index()
    daily_stats['crack_rate'] = (daily_stats['cracks_found'] / daily_stats['total_analyses'] * 100).round(1)
    
    # Deux colonnes pour les graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Graphique du nombre d'analyses par jour
        fig_analyses = px.line(
            daily_stats, 
            x='date', 
            y='total_analyses',
            title='📊 Analyses par Jour',
            labels={'total_analyses': 'Nombre d\'analyses', 'date': 'Date'}
        )
        fig_analyses.update_traces(line_color='#667eea', line_width=3)
        fig_analyses.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_analyses, use_container_width=True)
    
    with col2:
        # Graphique du taux de fissures
        fig_cracks = px.bar(
            daily_stats,
            x='date',
            y='crack_rate',
            title='⚠️ Taux de Fissures par Jour (%)',
            labels={'crack_rate': 'Taux de fissures (%)', 'date': 'Date'}
        )
        fig_cracks.update_traces(marker_color='#ff6b6b')
        fig_cracks.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_cracks, use_container_width=True)

def show_method_analysis(df):
    """Analyse par méthode de détection."""
    st.markdown("## 🔬 Analyse par Méthode")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Répartition des méthodes
        method_counts = df['method'].value_counts()
        fig_methods = px.pie(
            values=method_counts.values,
            names=method_counts.index,
            title='Répartition des Méthodes Utilisées',
            color_discrete_map={
                'Deep Learning': '#4CAF50',
                'OpenCV': '#FF9800'
            }
        )
        st.plotly_chart(fig_methods, use_container_width=True)
    
    with col2:
        # Comparaison des performances
        method_stats = df.groupby('method').agg({
            'confidence': 'mean',
            'processing_time': 'mean',
            'has_crack': 'mean'
        }).round(3)
        
        fig_comparison = go.Figure()
        
        fig_comparison.add_trace(go.Bar(
            name='Confiance Moyenne',
            x=method_stats.index,
            y=method_stats['confidence'] * 100,
            marker_color='#4CAF50'
        ))
        
        fig_comparison.update_layout(
            title='Comparaison des Performances',
            yaxis_title='Confiance (%)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig_comparison, use_container_width=True)

def show_recent_analyses(df):
    """Affiche l'historique récent des analyses."""
    st.markdown("## 🔍 Analyses Récentes")
    
    # Prendre les 20 analyses les plus récentes
    recent_df = df.nlargest(20, 'datetime').copy()
    
    # Préparer l'affichage
    recent_df['Status'] = recent_df['has_crack'].map({0: '✅ Saine', 1: '⚠️ Fissurée'})
    recent_df['Confiance'] = (recent_df['confidence'] * 100).round(1).astype(str) + '%'
    recent_df['Surface Fissurée'] = recent_df['crack_surface'].round(2).astype(str) + '%'
    recent_df['Temps'] = recent_df['processing_time'].round(1).astype(str) + 's'
    recent_df['Date/Heure'] = recent_df['datetime'].dt.strftime('%d/%m/%Y %H:%M')
    
    # Colonnes à afficher
    display_columns = ['Date/Heure', 'image_name', 'Status', 'Confiance', 'Surface Fissurée', 'method', 'Temps']
    display_df = recent_df[display_columns].copy()
    display_df.columns = ['Date/Heure', 'Image', 'Statut', 'Confiance', 'Surface Fissurée', 'Méthode', 'Temps']
    
    # Affichage avec style
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Statut": st.column_config.TextColumn(width="medium"),
            "Confiance": st.column_config.ProgressColumn(
                width="small",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            )
        }
    )

def create_csv_export(df):
    """Crée un export CSV des données d'analyse."""
    # Préparer les données pour l'export
    export_df = df.copy()
    
    # Formater les colonnes
    export_df['Date'] = export_df['datetime'].dt.strftime('%d/%m/%Y')
    export_df['Heure'] = export_df['datetime'].dt.strftime('%H:%M:%S')
    export_df['Fissure Détectée'] = export_df['has_crack'].map({0: 'Non', 1: 'Oui'})
    export_df['Confiance (%)'] = (export_df['confidence'] * 100).round(1)
    export_df['Surface Fissurée (%)'] = export_df['crack_surface'].round(2)
    export_df['Temps de Traitement (s)'] = export_df['processing_time'].round(2)
    
    # Sélectionner et renommer les colonnes
    columns_mapping = {
        'Date': 'Date',
        'Heure': 'Heure',
        'image_name': 'Nom de l\'Image',
        'Fissure Détectée': 'Fissure Détectée',
        'Confiance (%)': 'Confiance (%)',
        'Surface Fissurée (%)': 'Surface Fissurée (%)',
        'method': 'Méthode',
        'Temps de Traitement (s)': 'Temps de Traitement (s)'
    }
    
    export_df = export_df[list(columns_mapping.keys())].rename(columns=columns_mapping)
    
    return export_df.to_csv(index=False, encoding='utf-8-sig')

def create_pdf_report(df):
    """Crée un rapport PDF des analyses."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        textColor=colors.darkblue
    )
    
    normal_style = styles['Normal']
    
    # Titre principal
    story.append(Paragraph("📊 Rapport d'Analyses - Tableau de Bord", title_style))
    story.append(Spacer(1, 20))
    
    # Informations générales
    story.append(Paragraph("Informations Générales", subtitle_style))
    
    total_analyses = len(df)
    total_cracks = df['has_crack'].sum()
    crack_rate = (total_cracks / total_analyses) * 100 if total_analyses > 0 else 0
    avg_confidence = df['confidence'].mean() * 100
    avg_processing_time = df['processing_time'].mean()
    
    general_info = [
        ['Métrique', 'Valeur'],
        ['Total des Analyses', f"{total_analyses:,}"],
        ['Fissures Détectées', f"{total_cracks:,} ({crack_rate:.1f}%)"],
        ['Confiance Moyenne', f"{avg_confidence:.1f}%"],
        ['Temps de Traitement Moyen', f"{avg_processing_time:.2f} secondes"],
        ['Période d\'Analyse', f"Du {df['datetime'].min().strftime('%d/%m/%Y')} au {df['datetime'].max().strftime('%d/%m/%Y')}"]
    ]
    
    general_table = Table(general_info)
    general_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(general_table)
    story.append(Spacer(1, 20))
    
    # Analyse par méthode
    story.append(Paragraph("Analyse par Méthode", subtitle_style))
    
    method_stats = df.groupby('method').agg({
        'confidence': 'mean',
        'processing_time': 'mean',
        'has_crack': 'mean'
    }).round(3)
    
    method_data = [['Méthode', 'Confiance Moyenne (%)', 'Temps Moyen (s)', 'Taux de Fissures (%)']]
    for method, stats in method_stats.iterrows():
        method_data.append([
            method,
            f"{(stats['confidence'] * 100):.1f}",
            f"{stats['processing_time']:.2f}",
            f"{(stats['has_crack'] * 100):.1f}"
        ])
    
    method_table = Table(method_data)
    method_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(method_table)
    story.append(Spacer(1, 20))
    
    # Dernières analyses
    story.append(Paragraph("Dernières Analyses", subtitle_style))
    
    recent_df = df.nlargest(10, 'datetime').copy()
    recent_df['Date'] = recent_df['datetime'].dt.strftime('%d/%m/%Y')
    recent_df['Fissure'] = recent_df['has_crack'].map({0: 'Non', 1: 'Oui'})
    recent_df['Confiance (%)'] = (recent_df['confidence'] * 100).round(1)
    
    recent_data = [['Date', 'Image', 'Fissure', 'Confiance (%)', 'Méthode']]
    for _, row in recent_df.iterrows():
        recent_data.append([
            row['Date'],
            row['image_name'][:20] + '...' if len(row['image_name']) > 20 else row['image_name'],
            row['Fissure'],
            f"{row['Confiance (%)']:.1f}",
            row['method']
        ])
    
    recent_table = Table(recent_data)
    recent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7)
    ]))
    
    story.append(recent_table)
    story.append(Spacer(1, 20))
    
    # Pied de page
    story.append(Paragraph(f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", normal_style))
    
    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def show_export_options(df):
    """Options d'export des données."""
    st.markdown("## 💾 Export des Données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export CSV
        csv_data = create_csv_export(df)
        st.download_button(
            label="📊 Exporter CSV",
            data=csv_data.encode('utf-8-sig'),
            file_name=f"tableau_bord_analyses_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_csv_dashboard"
        )
    
    with col2:
        # Export PDF
        if st.button("📈 Générer Rapport PDF", use_container_width=True, key="generate_pdf_dashboard"):
            with st.spinner("📄 Génération du rapport PDF..."):
                pdf_data = create_pdf_report(df)
                
                st.download_button(
                    label="📄 Télécharger PDF",
                    data=pdf_data,
                    file_name=f"rapport_tableau_bord_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_pdf_dashboard"
                )
    
    # Informations sur les exports
    st.info("""
    📝 **Exports disponibles :**
    - **CSV** : Données complètes des analyses au format tableur
    - **PDF** : Rapport détaillé avec statistiques et graphiques
    """)

def main():
    """Fonction principale de la page."""
    setup_page()
    
    # Génération des données d'exemple
    with st.spinner("📊 Chargement des données..."):
        df = generate_sample_data()
    
    # Affichage des sections
    show_metrics_overview(df)
    
    st.markdown("---")
    show_time_series_charts(df)
    
    st.markdown("---")
    show_method_analysis(df)
    
    st.markdown("---")
    show_recent_analyses(df)
    
    st.markdown("---")
    show_export_options(df)
    
    # Note sur les données
    st.info("""
    📝 **Note**: Cette page affiche des données d'exemple générées aléatoirement. 
    Dans une version de production, ces données proviendraient d'une base de données 
    stockant l'historique réel des analyses effectuées.
    """)

if __name__ == "__main__":
    main()