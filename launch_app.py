#!/usr/bin/env python3
"""
Script de lancement de l'application de détection de fissures
============================================================

Ce script lance l'application Streamlit avec une configuration optimisée
et ouvre automatiquement le navigateur.
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_requirements():
    """Vérifie que les dépendances sont installées."""
    try:
        import streamlit
        print("✅ Streamlit disponible")
    except ImportError:
        print("❌ Streamlit non installé. Installez avec: pip install streamlit")
        return False
    
    try:
        import torch
        print("✅ PyTorch disponible")
    except ImportError:
        print("❌ PyTorch non installé. Installez avec: pip install torch")
        return False
    
    return True

def check_config_files():
    """Vérifie la présence des fichiers de configuration."""
    config_files = [
        ".streamlit/config.toml",
        "pyproject.toml",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in config_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  Fichiers de configuration manquants:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("   L'application peut fonctionner avec les paramètres par défaut.")
    else:
        print("✅ Tous les fichiers de configuration sont présents")

def check_models():
    """Vérifie la présence des modèles IA."""
    models_dir = Path("models")
    classification_model = models_dir / "classification" / "best_classification_model.pth"
    segmentation_model = models_dir / "segmentation" / "best_unet_model.pth"
    
    missing_models = []
    if not classification_model.exists():
        missing_models.append("Modèle de classification")
    if not segmentation_model.exists():
        missing_models.append("Modèle de segmentation")
    
    if missing_models:
        print("⚠️  Modèles IA manquants:")
        for model in missing_models:
            print(f"   - {model}")
        print("   L'application utilisera des méthodes alternatives.")
    else:
        print("✅ Tous les modèles IA sont présents")

def launch_streamlit():
    """Lance l'application Streamlit."""
    print("\n🚀 Lancement de l'application...")
    print("=" * 50)
    
    # Configuration des arguments Streamlit
    streamlit_args = [
        "streamlit", "run", "app.py",
        "--server.headless", "false",
        "--server.runOnSave", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        # Lance Streamlit
        process = subprocess.Popen(streamlit_args)
        
        # Attend un peu puis ouvre le navigateur
        time.sleep(3)
        webbrowser.open("http://localhost:8501")
        
        print("🌐 Application ouverte dans le navigateur: http://localhost:8501")
        print("📱 Interface mobile disponible sur le même port")
        print("\n💡 Pour arrêter l'application, appuyez sur Ctrl+C")
        
        # Attend que le processus se termine
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application...")
        process.terminate()
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        return False
    
    return True

def main():
    """Fonction principale."""
    print("🏗️  Application de Détection de Fissures")
    print("=" * 50)
    
    # Vérifications préliminaires
    print("\n🔍 Vérification des prérequis...")
    if not check_requirements():
        print("\n❌ Prérequis manquants. Installez les dépendances avec:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n📁 Vérification des fichiers de configuration...")
    check_config_files()
    
    print("\n🧠 Vérification des modèles IA...")
    check_models()
    
    # Lancement de l'application
    print("\n" + "=" * 50)
    if not launch_streamlit():
        sys.exit(1)

if __name__ == "__main__":
    main()
