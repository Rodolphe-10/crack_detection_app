# 🏗️ Détection de Fissures

Application Streamlit professionnelle pour la détection et segmentation de fissures dans les structures en béton.

## 🚀 Fonctionnalités

- **🔍 Détection Simple**: Analyse d'image avec classification et segmentation
- **📊 Analyse Batch**: Traitement de plusieurs images simultanément  
- **📹 Temps Réel**: Inspection en direct via webcam
- **📈 Tableau de Bord**: Historique et statistiques
- **💬 Assistant IA**: Chat avec Groq pour aide contextuelle
- **📄 Rapports**: Export PDF/Excel pour documentation

## 📋 Prérequis

- Python 3.8+
- GPU recommandé (CUDA/MPS) pour de meilleures performances
- Clé API Groq (optionnelle, pour le chat assistant)

## 🛠️ Installation

### 1. Cloner et installer les dépendances

```bash
cd crack_detection_app
pip install -r requirements.txt
```

### 2. Configurer les modèles

Copiez vos modèles entraînés dans les dossiers appropriés :

```
models/
├── classification/
│   └── best_classification_model.pth
└── segmentation/
    └── best_segmentation_model.pth
```

### 3. Configuration Groq (optionnelle)

Pour activer le chat assistant, configurez votre clé API Groq :

#### Méthode 1: Variable d'environnement
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

#### Méthode 2: Secrets Streamlit
1. Copiez le template : `cp .streamlit/secrets.toml.example .streamlit/secrets.toml`
2. Éditez le fichier `.streamlit/secrets.toml` :
```toml
GROQ_API_KEY = "your_groq_api_key_here"

[email]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password_here"
```

## 🏃‍♂️ Lancement

### Méthode 1: Script de lancement optimisé (Recommandé)
```bash
python launch_app.py
```
- ✅ Vérifications automatiques des prérequis
- ✅ Ouverture automatique du navigateur
- ✅ Configuration optimisée
- ✅ Gestion d'erreurs

### Méthode 2: Fichier batch (Windows)
Double-cliquez sur `launch_app.bat`

### Méthode 3: Lancement simple
```bash
streamlit run app.py
```

### Méthode 4: Paramètres explicites
```bash
streamlit run app.py --server.headless false --server.runOnSave true
```

**Note**: Si le navigateur ne s'ouvre pas automatiquement, ouvrez manuellement : http://localhost:8501

### Déploiement Hugging Face Spaces

1. Créez un nouveau Space sur [Hugging Face](https://huggingface.co/spaces)
2. Sélectionnez "Streamlit" comme SDK
3. Uploadez tous les fichiers
4. Configurez les secrets dans les paramètres du Space

## 📁 Structure du Projet

```
crack_detection_app/
├── app.py                          # Application principale
├── launch_app.py                   # Script de lancement optimisé
├── launch_app.bat                  # Script batch Windows
├── pages/
│   ├── 🔍_Detection_Simple.py      # Page de détection simple
│   ├── 📊_Analyse_Batch.py         # Traitement batch
│   ├── 📹_Detection_Temps_Reel.py  # Webcam temps réel
│   └── 📈_Tableau_de_Bord.py       # Dashboard
├── utils/
│   ├── model_loader.py             # Chargement des modèles
│   ├── chat_assistant.py           # Assistant Groq
│   ├── image_processor.py          # Traitement d'images
│   └── visualizer.py               # Visualisations
├── config/
│   └── config.py                   # Configuration générale
├── .streamlit/
│   ├── config.toml                 # Configuration Streamlit
│   └── secrets.toml.example        # Template pour les secrets
├── models/
│   ├── classification/             # Modèles de classification
│   └── segmentation/               # Modèles de segmentation
├── pyproject.toml                  # Configuration du projet Python
├── requirements.txt                # Dépendances Python
├── .gitignore                      # Fichiers à ignorer par Git
└── README.md                       # Documentation
```

## 🎯 Performances des Modèles

### Classification (ResNet50)
- **Accuracy**: 87.93%
- **Precision**: 88.81%
- **Recall**: 86.80%
- **F1-Score**: 87.80%

### Segmentation (UNet)
- **Dice Score**: 0.85
- **IoU**: 0.78

## 🎨 Thème et Design

L'application utilise un thème professionnel inspiré du secteur de la construction :
- **Couleurs primaires**: Gris béton, bleu acier
- **Accents**: Orange sécurité pour les alertes
- **Interface**: Moderne et responsive
- **UX**: Optimisée pour les ingénieurs et techniciens

## 🔧 Configuration Avancée

### Fichiers de Configuration

#### pyproject.toml
Configuration du projet Python avec :
- Métadonnées du projet
- Dépendances et versions
- Configuration des outils de développement
- Scripts d'installation

#### .streamlit/config.toml
Configuration Streamlit avec :
- Thème sombre professionnel
- Paramètres du serveur
- Configuration de l'interface
- Limites de taille de fichier

#### .streamlit/secrets.toml
Secrets et clés API (créé à partir de `secrets.toml.example`) :
- Clé API Groq
- Configuration SMTP
- Paramètres personnalisés

### Seuils de Détection
- **Classification**: 0.7 (ajustable dans l'interface)
- **Segmentation**: 0.5 (ajustable dans l'interface)

### Limites
- **Taille max fichier**: 200 MB
- **Formats supportés**: JPG, PNG, BMP, TIFF
- **Batch max**: 20 images

## 🐛 Dépannage

### Modèles non trouvés
```
❌ Modèle de classification manquant
```
**Solution**: Vérifiez que `best_classification_model.pth` est dans `models/classification/`

### Chat assistant indisponible
```
⚠️ Clé API Groq non configurée
```
**Solution**: Configurez la variable d'environnement `GROQ_API_KEY`

### Erreurs de mémoire
**Solution**: 
- Réduisez la taille des images
- Utilisez un GPU si disponible
- Fermez les autres applications

## 📞 Support

Pour toute question ou problème :
1. Vérifiez la configuration des modèles
2. Consultez les logs dans la console
3. Utilisez le chat assistant intégré pour de l'aide

## 📄 Licence

Application développée pour l'inspection professionnelle de structures en béton.

---

**Dernière mise à jour**: 2025