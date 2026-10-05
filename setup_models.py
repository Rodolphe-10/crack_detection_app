#!/usr/bin/env python3
"""
Script de configuration des modèles
==================================

Ce script copie les modèles entraînés dans l'application.
"""

import shutil
from pathlib import Path
import os

def setup_models():
    """Copie les modèles depuis les projets d'entraînement."""
    
    # Chemins source
    classification_source = Path("../Modele_Classification/best_classification_model.pth")
    segmentation_source = Path("../Modele_DeepLearning/best_unet_model.pth")
    
    # Chemins destination
    classification_dest = Path("models/classification/best_classification_model.pth")
    segmentation_dest = Path("models/segmentation/best_unet_model.pth")
    
    print("🔄 Configuration des modèles...")
    
    # Copier le modèle de classification
    if classification_source.exists():
        shutil.copy2(classification_source, classification_dest)
        print(f"✅ Modèle de classification copié: {classification_dest}")
    else:
        print(f"❌ Modèle de classification non trouvé: {classification_source}")
    
    # Copier le modèle de segmentation
    if segmentation_source.exists():
        shutil.copy2(segmentation_source, segmentation_dest)
        print(f"✅ Modèle de segmentation copié: {segmentation_dest}")
    else:
        print(f"❌ Modèle de segmentation non trouvé: {segmentation_source}")
    
    print("\n🎉 Configuration terminée!")
    print("\nPour lancer l'application:")
    print("streamlit run app.py")

if __name__ == "__main__":
    setup_models()