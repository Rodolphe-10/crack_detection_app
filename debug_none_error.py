#!/usr/bin/env python3
"""
Script de debug pour identifier l'erreur None dans int()
====================================================
"""

import sys
import traceback
import numpy as np
from pathlib import Path

# Ajouter le répertoire du projet au path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_email_sender():
    """Debug EmailSender"""
    print("🔧 Debug EmailSender...")
    try:
        from utils.email_sender import EmailSender
        sender = EmailSender()
        print(f"✅ smtp_port: {sender.smtp_port} (type: {type(sender.smtp_port)})")
        return True
    except Exception as e:
        print(f"❌ Erreur EmailSender: {e}")
        traceback.print_exc()
        return False

def debug_image_processor():
    """Debug image processor"""
    print("🔧 Debug image processor...")
    try:
        from utils.image_processor import run_classification_analysis
        
        # Test avec modèle None
        test_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = run_classification_analysis(None, test_image)
        print(f"✅ run_classification_analysis(None): {result}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur image_processor: {e}")
        traceback.print_exc()
        return False

def debug_model_loading():
    """Debug model loading"""
    print("🔧 Debug model loading...")
    try:
        from utils.model_loader import load_models
        models = load_models()
        classification_model, segmentation_model = models
        
        print(f"✅ Classification model: {classification_model is not None}")
        print(f"✅ Segmentation model: {segmentation_model is not None}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur model loading: {e}")
        traceback.print_exc()
        return False

def debug_streamlit_imports():
    """Debug Streamlit imports"""
    print("🔧 Debug Streamlit imports...")
    try:
        import streamlit as st
        print("✅ Streamlit importé")
        
        # Simuler une session Streamlit
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        return True
    except Exception as e:
        print(f"❌ Erreur Streamlit: {e}")
        traceback.print_exc()
        return False

def main():
    """Fonction principale de debug"""
    print("🐛 Debug de l'erreur None dans int()")
    print("=" * 50)
    
    tests = [
        debug_streamlit_imports,
        debug_email_sender,
        debug_image_processor,
        debug_model_loading,
    ]
    
    for test in tests:
        print()
        try:
            result = test()
            if not result:
                print("❌ Test échoué")
        except Exception as e:
            print(f"❌ Exception dans le test: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 Debug terminé")

if __name__ == "__main__":
    main()

